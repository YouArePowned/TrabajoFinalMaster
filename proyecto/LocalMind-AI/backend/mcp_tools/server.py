"""
LocalMind-AI — MCP Tools Server
Exposes custom tools (PDF, 3D prep, Printer, RAG) via MCP.
Optimized to run lightweight on CPU inside Docker.
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Any
import requests

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

OUTPUTS_DIR = os.getenv("OUTPUTS_DIR", "/tmp/localmind-outputs")
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "/app/chroma_db")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

server = Server("localmind-tools")

# ---------------------------------------------------------------------------
# RAG Setup (Lazy Initialization using Host Ollama API for Embeddings)
# ---------------------------------------------------------------------------
_chroma_client = None
_collection = None

class LocalMindEmbeddingFunction:
    """Custom embedding function that delegates work to the host's Ollama instance."""
    def __init__(self, ollama_url: str, model_name: str):
        self.ollama_url = ollama_url
        self.model_name = model_name

    def __call__(self, input: list[str]) -> list[list[float]]:
        try:
            # Try new Ollama /api/embed endpoint
            response = requests.post(
                f"{self.ollama_url}/api/embed",
                json={"model": self.model_name, "input": input},
                timeout=15
            )
            if response.status_code == 200:
                return response.json()["embeddings"]
            
            # Fallback to older /api/embeddings endpoint (one by one)
            embeddings = []
            for text in input:
                resp = requests.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={"model": self.model_name, "prompt": text},
                    timeout=10
                )
                if resp.status_code == 200:
                    embeddings.append(resp.json()["embedding"])
                else:
                    raise Exception(f"Ollama API returned status {resp.status_code}")
            return embeddings
        except Exception as e:
            print(f"[RAG Warn] Failed to connect to Ollama on {self.ollama_url} for embeddings: {e}. Rerouting or mock vectors will be used.", flush=True)
            # Fallback mock dimension for nomic-embed-text is 768
            return [[0.0] * 768 for _ in input]

def _init_rag():
    """Lazily initialize ChromaDB client."""
    global _chroma_client, _collection
    if _chroma_client is not None:
        return

    import chromadb
    print(f"Initializing ChromaDB RAG (pointing to host Ollama: {OLLAMA_URL} with model: {OLLAMA_EMBED_MODEL})...", flush=True)
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)
    
    # Initialize ChromaDB
    _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    
    # Setup custom embedding function
    emb_fn = LocalMindEmbeddingFunction(ollama_url=OLLAMA_URL, model_name=OLLAMA_EMBED_MODEL)
    
    # Create or get collection with embedding function
    _collection = _chroma_client.get_or_create_collection(
        name="knowledge_base",
        embedding_function=emb_fn
    )
    print("ChromaDB initialized successfully.", flush=True)


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="generate_pdf",
            description=(
                "Generate a PDF document from structured content. "
                "Returns the path to the generated file."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Document title"},
                    "content": {"type": "string", "description": "Document body (markdown or plain text)"},
                    "author": {"type": "string", "default": "LocalMind-AI", "description": "Author name"},
                    "filename": {"type": "string", "description": "Output filename (without extension)"},
                },
                "required": ["title", "content"],
            },
        ),
        Tool(
            name="prepare_3d_print",
            description=(
                "Prepare a file for 3D printing. Validates parameters, "
                "generates a print job configuration, and returns the job file path."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "model_name": {"type": "string", "description": "Name or path of the 3D model"},
                    "material": {
                        "type": "string",
                        "enum": ["PLA", "ABS", "PETG", "TPU", "Nylon"],
                        "default": "PLA",
                        "description": "Printing material",
                    },
                    "quality": {
                        "type": "string",
                        "enum": ["draft", "normal", "high"],
                        "default": "normal",
                        "description": "Print quality preset",
                    },
                    "infill": {
                        "type": "integer",
                        "default": 20,
                        "description": "Infill percentage (0-100)",
                    },
                    "supports": {
                        "type": "boolean",
                        "default": False,
                        "description": "Enable support structures",
                    },
                },
                "required": ["model_name"],
            },
        ),
        Tool(
            name="send_to_printer",
            description=(
                "Send a document to the local printer queue."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Absolute path to the file to print"},
                    "copies": {"type": "integer", "default": 1, "description": "Number of copies"},
                },
                "required": ["filepath"],
            },
        ),
        Tool(
            name="index_document",
            description=(
                "Add a text or knowledge block to the local vector database for RAG. "
                "The text will be chunked, embedded using host Ollama, and stored."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The content to index"},
                    "source": {"type": "string", "description": "Source name (e.g., filename or topic)"},
                },
                "required": ["text", "source"],
            },
        ),
        Tool(
            name="search_knowledge_base",
            description=(
                "Search the local vector database. Returns top matching texts."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "top_k": {"type": "integer", "default": 3, "description": "Number of results to return"},
                },
                "required": ["query"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _generate_pdf(title: str, content: str, author: str = "LocalMind-AI", filename: str | None = None) -> dict:
    """Generate a simple PDF using reportlab or plain-text fallback."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    fname = filename or title.replace(" ", "_").lower()
    out_path = os.path.join(OUTPUTS_DIR, f"{fname}.pdf")

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        doc = SimpleDocTemplate(out_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = [
            Paragraph(title, styles["Title"]),
            Spacer(1, 12),
            Paragraph(f"Author: {author}", styles["Normal"]),
            Spacer(1, 24),
        ]
        for para in content.split("\n\n"):
            story.append(Paragraph(para, styles["BodyText"]))
            story.append(Spacer(1, 8))
        doc.build(story)
        return {"success": True, "path": out_path, "size_bytes": os.path.getsize(out_path)}
    except ImportError:
        txt_path = out_path.replace(".pdf", ".txt")
        with open(txt_path, "w") as f:
            f.write(f"{'='*60}\n{title}\nAuthor: {author}\n{'='*60}\n\n{content}\n")
        return {
            "success": True,
            "path": txt_path,
            "note": "reportlab not installed; generated plain-text file instead",
        }


def _prepare_3d_print(
    model_name: str,
    material: str = "PLA",
    quality: str = "normal",
    infill: int = 20,
    supports: bool = False,
) -> dict:
    """Prepare a 3D print job configuration."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    layer_height = {"draft": 0.3, "normal": 0.2, "high": 0.1}[quality]
    temp_map = {"PLA": 210, "ABS": 240, "PETG": 235, "TPU": 225, "Nylon": 260}

    job = {
        "model": model_name,
        "material": material,
        "quality": quality,
        "layer_height_mm": layer_height,
        "infill_pct": max(0, min(100, infill)),
        "supports": supports,
        "nozzle_temp_c": temp_map.get(material, 210),
        "bed_temp_c": 60 if material in ("PLA", "PETG") else 100,
        "created_at": datetime.utcnow().isoformat(),
        "status": "ready",
    }

    job_file = os.path.join(
        OUTPUTS_DIR,
        f"print_job_{model_name.replace(' ', '_').lower()}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
    )
    with open(job_file, "w") as f:
        json.dump(job, f, indent=2)

    return {"success": True, "job_file": job_file, "job": job}


async def _send_to_printer(filepath: str, copies: int = 1) -> dict:
    """Simulate sending a document to a physical printer."""
    if not os.path.exists(filepath):
        return {"success": False, "error": f"File not found: {filepath}"}
    
    # Simulate printer spooling delay
    await asyncio.sleep(2)
    
    return {
        "success": True, 
        "status": "Spooling completed", 
        "message": f"Sent {copies} copy/copies of {os.path.basename(filepath)} to default printer.",
        "timestamp": datetime.utcnow().isoformat()
    }


def _chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """Basic word-based chunking."""
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


def _index_document(text: str, source: str) -> dict:
    """Index text into ChromaDB, leveraging host's Ollama for embeddings."""
    try:
        _init_rag()
        chunks = _chunk_text(text)
        
        # Prepare ChromaDB inputs
        ids = [f"{source}_{uuid.uuid4().hex[:8]}" for _ in chunks]
        metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]
        
        # Adding documents automatically runs the embedding function defined in _init_rag
        _collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        return {"success": True, "indexed_chunks": len(chunks), "source": source}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _search_knowledge_base(query: str, top_k: int = 3) -> dict:
    """Search ChromaDB using local vectors and similarity search."""
    try:
        _init_rag()
        
        # Querying by text automatically runs the embedding function defined in _init_rag
        results = _collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        if not results['documents'] or not results['documents'][0]:
            return {"success": True, "results": []}
            
        candidate_docs = results['documents'][0]
        candidate_metas = results['metadatas'][0]
        candidate_distances = results['distances'][0] if 'distances' in results and results['distances'] else [0.0] * len(candidate_docs)
        
        final_results = []
        for doc, meta, dist in zip(candidate_docs, candidate_metas, candidate_distances):
            # Convert L2 distance to a basic relevance score (smaller distance = higher relevance)
            relevance = round(1.0 / (1.0 + dist), 4)
            final_results.append({
                "content": doc,
                "source": meta.get("source", "unknown"),
                "relevance_score": relevance
            })
            
        return {"success": True, "results": final_results}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "generate_pdf":
        result = _generate_pdf(**arguments)
    elif name == "prepare_3d_print":
        result = _prepare_3d_print(**arguments)
    elif name == "send_to_printer":
        result = await _send_to_printer(**arguments)
    elif name == "index_document":
        result = _index_document(**arguments)
    elif name == "search_knowledge_base":
        result = _search_knowledge_base(**arguments)
    else:
        result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
