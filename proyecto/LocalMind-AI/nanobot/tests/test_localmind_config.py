import asyncio
import json
import os
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from nanobot.api.server import create_app

try:
    from aiohttp.test_utils import TestClient, TestServer
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    return agent


@pytest.fixture
def app(mock_agent):
    return create_app(mock_agent, model_name="test-model", request_timeout=10.0)


@pytest_asyncio.fixture
async def aiohttp_client():
    clients = []

    async def _make_client(app):
        client = TestClient(TestServer(app))
        await client.start_server()
        clients.append(client)
        return client

    try:
        yield _make_client
    finally:
        for c in clients:
            await c.close()


@pytest.mark.asyncio
@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp is not installed")
async def test_get_config(app, aiohttp_client):
    client = await aiohttp_client(app)
    
    # Run GET /localmind/config
    resp = await client.get("/localmind/config")
    assert resp.status == 200
    data = await resp.json()
    
    # Assert expected structure
    assert "backend_type" in data
    assert "selected_model" in data
    assert "apiKey" in data
    assert "enable_engram" in data
    assert "ollama" in data
    assert "mlx" in data


@pytest.mark.asyncio
@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp is not installed")
async def test_post_config_validation(app, aiohttp_client):
    client = await aiohttp_client(app)
    
    # Run POST /localmind/config with missing selected_model
    resp = await client.post("/localmind/config", json={
        "backend_type": "mlx",
        "apiKey": "test-key"
    })
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data
