"""OpenAI-compatible HTTP API server for a fixed nanobot session.

Provides /v1/chat/completions and /v1/models endpoints.
All requests route to a single persistent API session.
"""

from __future__ import annotations

import asyncio
import json as _json
import time
import uuid
from typing import Any

import os
import aiohttp
from aiohttp import web
from loguru import logger

from nanobot.config.paths import get_media_dir
from nanobot.utils.helpers import safe_filename
from nanobot.utils.media_decode import (
    FileSizeExceeded as _FileSizeExceeded,
    MAX_FILE_SIZE,
    save_base64_data_url as _save_base64_data_url,
)
from nanobot.utils.runtime import EMPTY_FINAL_RESPONSE_MESSAGE

__all__ = (
    "MAX_FILE_SIZE",
    "_FileSizeExceeded",
    "_save_base64_data_url",
    "create_app",
    "handle_chat_completions",
)


API_SESSION_KEY = "api:default"
API_CHAT_ID = "default"


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


def _error_json(status: int, message: str, err_type: str = "invalid_request_error") -> web.Response:
    return web.json_response(
        {"error": {"message": message, "type": err_type, "code": status}},
        status=status,
    )


def _chat_completion_response(content: str, model: str) -> dict[str, Any]:
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


def _response_text(value: Any) -> str:
    """Normalize process_direct output to plain assistant text."""
    if value is None:
        return ""
    if hasattr(value, "content"):
        return str(getattr(value, "content") or "")
    return str(value)

# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------


def _sse_chunk(delta: str, model: str, chunk_id: str, finish_reason: str | None = None) -> bytes:
    """Format a single OpenAI-compatible SSE chunk."""
    payload = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {"content": delta} if delta else {},
                "finish_reason": finish_reason,
            }
        ],
    }
    return f"data: {_json.dumps(payload)}\n\n".encode()


_SSE_DONE = b"data: [DONE]\n\n"

# ---------------------------------------------------------------------------
# Upload helpers
# ---------------------------------------------------------------------------


def _parse_json_content(body: dict) -> tuple[str, list[str]]:
    """Parse JSON request body. Returns (text, media_paths)."""
    messages = body.get("messages")
    if not isinstance(messages, list) or len(messages) != 1:
        raise ValueError("Only a single user message is supported")
    message = messages[0]
    if not isinstance(message, dict) or message.get("role") != "user":
        raise ValueError("Only a single user message is supported")

    user_content = message.get("content", "")
    media_dir = get_media_dir("api")
    media_paths: list[str] = []

    if isinstance(user_content, list):
        text_parts: list[str] = []
        for part in user_content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text":
                text_parts.append(part.get("text", ""))
            elif part.get("type") == "image_url":
                url = part.get("image_url", {}).get("url", "")
                if url.startswith("data:"):
                    saved = _save_base64_data_url(url, media_dir)
                    if saved:
                        media_paths.append(saved)
                elif url:
                    raise ValueError(
                        "Remote image URLs are not supported. "
                        "Use base64 data URLs or upload files via multipart/form-data."
                    )
        text = " ".join(text_parts)
    elif isinstance(user_content, str):
        text = user_content
    else:
        raise ValueError("Invalid content format")

    return text, media_paths


async def _parse_multipart(request: web.Request) -> tuple[str, list[str], str | None, str | None]:
    """Parse multipart/form-data. Returns (text, media_paths, session_id, model)."""
    media_dir = get_media_dir("api")
    reader = await request.multipart()
    text = ""
    session_id = None
    model = None
    media_paths: list[str] = []

    while True:
        part = await reader.next()
        if part is None:
            break
        if part.name == "message":
            text = (await part.read()).decode("utf-8")
        elif part.name == "session_id":
            session_id = (await part.read()).decode("utf-8").strip()
        elif part.name == "model":
            model = (await part.read()).decode("utf-8").strip()
        elif part.name == "files":
            raw = await part.read()
            if len(raw) > MAX_FILE_SIZE:
                raise _FileSizeExceeded(
                    f"File '{part.filename}' exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit"
                )
            base = safe_filename(part.filename or "upload.bin")
            filename = f"{uuid.uuid4().hex[:12]}_{base}"
            dest = media_dir / filename
            dest.write_bytes(raw)
            media_paths.append(str(dest))

    if not text:
        text = "请分析上传的文件"

    return text, media_paths, session_id, model


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


async def handle_chat_completions(request: web.Request) -> web.Response:
    """POST /v1/chat/completions — supports JSON and multipart/form-data."""
    content_type = request.content_type or ""
    if not isinstance(content_type, str):
        content_type = ""

    agent_loop = request.app["agent_loop"]
    timeout_s: float = request.app.get("request_timeout", 120.0)
    model_name: str = request.app.get("model_name", "nanobot")

    stream = False
    try:
        if content_type.startswith("multipart/"):
            text, media_paths, session_id, requested_model = await _parse_multipart(request)
        else:
            try:
                body = await request.json()
            except Exception:
                return _error_json(400, "Invalid JSON body")
            stream = body.get("stream", False)
            requested_model = body.get("model")
            text, media_paths = _parse_json_content(body)
            session_id = body.get("session_id")
    except ValueError as e:
        return _error_json(400, str(e))
    except _FileSizeExceeded as e:
        return _error_json(413, str(e), err_type="invalid_request_error")
    except Exception:
        logger.exception("Error parsing upload")
        return _error_json(413, "File too large or invalid upload")

    if requested_model and requested_model != model_name:
        return _error_json(400, f"Only configured model '{model_name}' is available")

    session_key = f"api:{session_id}" if session_id else API_SESSION_KEY
    session_locks: dict[str, asyncio.Lock] = request.app["session_locks"]
    session_lock = session_locks.setdefault(session_key, asyncio.Lock())

    logger.info(
        "API request session_key={} media={} text={} stream={}",
        session_key, len(media_paths), text[:80], stream,
    )
    # -- streaming path --
    if stream:
        resp = web.StreamResponse()
        resp.content_type = "text/event-stream"
        resp.headers["Cache-Control"] = "no-cache"
        resp.headers["Connection"] = "keep-alive"
        resp.enable_compression()
        await resp.prepare(request)

        chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        stream_failed = False

        async def _on_stream(token: str) -> None:
            await queue.put(token)

        async def _on_stream_end(*_a: Any, **_kw: Any) -> None:
            await queue.put(None)

        async def _run() -> None:
            nonlocal stream_failed
            try:
                async with session_lock:
                    await asyncio.wait_for(
                        agent_loop.process_direct(
                            content=text,
                            media=media_paths if media_paths else None,
                            session_key=session_key,
                            channel="api",
                            chat_id=API_CHAT_ID,
                            on_stream=_on_stream,
                            on_stream_end=_on_stream_end,
                        ),
                        timeout=timeout_s,
                    )
            except Exception:
                stream_failed = True
                logger.exception("Streaming error for session {}", session_key)
                await queue.put(None)

        task = asyncio.create_task(_run())
        try:
            while True:
                token = await queue.get()
                if token is None:
                    break
                await resp.write(_sse_chunk(token, model_name, chunk_id))
        finally:
            task.cancel()

        if not stream_failed:
            await resp.write(_sse_chunk("", model_name, chunk_id, finish_reason="stop"))
            await resp.write(_SSE_DONE)
        return resp

    # -- non-streaming path (original logic) --
    _FALLBACK = EMPTY_FINAL_RESPONSE_MESSAGE

    try:
        async with session_lock:
            try:
                response = await asyncio.wait_for(
                    agent_loop.process_direct(
                        content=text,
                        media=media_paths if media_paths else None,
                        session_key=session_key,
                        channel="api",
                        chat_id=API_CHAT_ID,
                    ),
                    timeout=timeout_s,
                )
                response_text = _response_text(response)

                if not response_text or not response_text.strip():
                    logger.warning("Empty response for session {}, retrying", session_key)
                    retry_response = await asyncio.wait_for(
                        agent_loop.process_direct(
                            content=text,
                            media=media_paths if media_paths else None,
                            session_key=session_key,
                            channel="api",
                            chat_id=API_CHAT_ID,
                        ),
                        timeout=timeout_s,
                    )
                    response_text = _response_text(retry_response)
                    if not response_text or not response_text.strip():
                        logger.warning("Empty response after retry, using fallback")
                        response_text = _FALLBACK

            except asyncio.TimeoutError:
                return _error_json(504, f"Request timed out after {timeout_s}s")
            except Exception:
                logger.exception("Error processing request for session {}", session_key)
                return _error_json(500, "Internal server error", err_type="server_error")
    except Exception:
        logger.exception("Unexpected API lock error for session {}", session_key)
        return _error_json(500, "Internal server error", err_type="server_error")

    return web.json_response(_chat_completion_response(response_text, model_name))


async def handle_models(request: web.Request) -> web.Response:
    """GET /v1/models"""
    model_name = request.app.get("model_name", "nanobot")
    return web.json_response(
        {
            "object": "list",
            "data": [
                {
                    "id": model_name,
                    "object": "model",
                    "created": 0,
                    "owned_by": "nanobot",
                }
            ],
        }
    )


async def handle_health(request: web.Request) -> web.Response:
    """GET /health"""
    return web.json_response({"status": "ok"})


# ---------------------------------------------------------------------------
# LocalMind Configuration API
# ---------------------------------------------------------------------------

ACTIVE_ENV_PATH = "/app/config/active_env.json"
CONFIG_PATH = "/app/config/config.json"

# Local testing fallbacks
if not os.path.exists(ACTIVE_ENV_PATH) and os.path.exists("backend/config/active_env.json"):
    ACTIVE_ENV_PATH = "backend/config/active_env.json"
if not os.path.exists(CONFIG_PATH) and os.path.exists("backend/config/config.json"):
    CONFIG_PATH = "backend/config/config.json"

async def cors_middleware(app, handler):
    async def middleware_handler(request):
        if request.method == "OPTIONS":
            response = web.Response()
        else:
            response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        return response
    return middleware_handler

async def handle_get_config(request: web.Request) -> web.Response:
    # 1. Load active_env.json
    env_data = {}
    if os.path.exists(ACTIVE_ENV_PATH):
        try:
            with open(ACTIVE_ENV_PATH, "r") as f:
                env_data = _json.load(f)
        except Exception:
            pass

    # 2. Load config.json
    config_data = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config_data = _json.load(f)
        except Exception:
            pass

    # 3. Retrieve model and provider info
    backend_type = env_data.get("BACKEND_TYPE", "ollama")
    selected_model = env_data.get("SELECTED_MODEL", "qwen2.5:7b")
    api_key = config_data.get("providers", {}).get("custom", {}).get("apiKey", "")
    enable_engram = env_data.get("ENABLE_ENGRAM", 0)

    # 4. Asynchronously fetch available Ollama models
    ollama_models = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://host.docker.internal:11434/api/tags", timeout=1.5) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    ollama_models = [m["name"] for m in res_json.get("models", [])]
    except Exception:
        pass

    # 5. Asynchronously fetch available oMLX models
    mlx_models = []
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get("http://host.docker.internal:8082/v1/models", headers=headers, timeout=1.5) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    mlx_models = [m["id"] for m in res_json.get("data", [])]
    except Exception:
        pass

    response_payload = {
        "backend_type": backend_type,
        "selected_model": selected_model,
        "apiKey": api_key,
        "enable_engram": enable_engram,
        "ollama": {
            "url": "http://localhost:11434",
            "models": ollama_models
        },
        "mlx": {
            "url": "http://localhost:8082",
            "models": mlx_models
        }
    }
    return web.json_response(response_payload)

async def handle_post_config(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return _error_json(400, "Invalid JSON body")

    backend_type = data.get("backend_type", "ollama")
    selected_model = data.get("selected_model")
    api_key = data.get("apiKey", "")
    enable_engram = data.get("enable_engram", 0)

    if not selected_model:
        return _error_json(400, "selected_model is required")

    # 1. Update active_env.json
    env_data = {}
    if os.path.exists(ACTIVE_ENV_PATH):
        try:
            with open(ACTIVE_ENV_PATH, "r") as f:
                env_data = _json.load(f)
        except Exception:
            pass
    env_data["BACKEND_TYPE"] = backend_type
    env_data["SELECTED_MODEL"] = selected_model
    env_data["ENABLE_ENGRAM"] = enable_engram
    
    # Save active_env.json
    try:
        os.makedirs(os.path.dirname(ACTIVE_ENV_PATH), exist_ok=True)
        with open(ACTIVE_ENV_PATH, "w") as f:
            _json.dump(env_data, f, indent=2)
    except Exception as e:
        return _error_json(500, f"Failed to save active_env.json: {e}")

    # 2. Update config.json
    config_data = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config_data = _json.load(f)
        except Exception:
            pass

    # Ensure sections exist
    config_data.setdefault("providers", {}).setdefault("custom", {})
    config_data.setdefault("agents", {}).setdefault("defaults", {})
    config_data.setdefault("tools", {}).setdefault("mcpServers", {})

    # Set apiBase based on provider
    if backend_type == "ollama":
        config_data["providers"]["custom"]["apiBase"] = "http://host.docker.internal:11434/v1"
        config_data["providers"]["custom"]["apiKey"] = ""
    else: # mlx
        config_data["providers"]["custom"]["apiBase"] = "http://host.docker.internal:8082/v1"
        config_data["providers"]["custom"]["apiKey"] = api_key

    config_data["agents"]["defaults"]["model"] = selected_model

    # Handle Engram MCP Server config
    if enable_engram == 1:
        config_data["tools"]["mcpServers"]["engram"] = {
            "command": "pnpm",
            "args": ["--package=engram-sdk", "dlx", "engram-mcp"],
            "env": {
                "ENGRAM_DATA_DIR": "/app/engram"
            }
        }
    else:
        config_data["tools"]["mcpServers"].pop("engram", None)

    # Save config.json
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            _json.dump(config_data, f, indent=2)
    except Exception as e:
        return _error_json(500, f"Failed to save config.json: {e}")

    # 3. Schedule asynchronous restart of the container
    async def schedule_restart():
        await asyncio.sleep(1.0)
        logger.info("Configuration updated from REST API. Restarting process...")
        import sys
        sys.exit(0)

    asyncio.create_task(schedule_restart())

    return web.json_response({
        "status": "ok",
        "message": "Config saved successfully. Restarting agent container to apply changes..."
    })


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app(
    agent_loop, model_name: str = "nanobot", request_timeout: float = 120.0
) -> web.Application:
    """Create the aiohttp application with CORS support.

    Args:
        agent_loop: An initialized AgentLoop instance.
        model_name: Model name reported in responses.
        request_timeout: Per-request timeout in seconds.
    """
    app = web.Application(client_max_size=20 * 1024 * 1024, middlewares=[cors_middleware])  # 20MB for base64 images
    app["agent_loop"] = agent_loop
    app["model_name"] = model_name
    app["request_timeout"] = request_timeout
    app["session_locks"] = {}  # per-user locks, keyed by session_key

    app.router.add_post("/v1/chat/completions", handle_chat_completions)
    app.router.add_get("/v1/models", handle_models)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/localmind/config", handle_get_config)
    app.router.add_post("/localmind/config", handle_post_config)
    return app
