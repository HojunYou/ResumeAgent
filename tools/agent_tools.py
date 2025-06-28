"""
tools.agent_tools
=================
Unified MCP‑compliant toolbox used by the LLM agent.

Exposed tools
-------------
• search_web(query)          → {"results": [...]}
• read_resource(uri)         → {"content": str}
• fetch_pdf_as_text(path)    → {"text": str}
• chat(messages, model)      → {"message": ...}
• embed_text(text)           → {"vector": [float]}
• chat_with_llm(prompt, context) → {"message": ...}
• save_tex_file(path, content) → {"path": str}
• save_similarity_csv(rows)  → {"ok": True}
"""

from __future__ import annotations
import pathlib
import requests
from typing import List
import fitz  # PyMuPDF

from mcp import service, tool, MCP

# --- MCP Service Definitions -------------------------------------------------

@service
class DocumentReader:
    """A service for reading various document types (PDF, HTML)."""
    @tool
    async def read(self, uri: str) -> str:
        """Reads content from a URI (file path or URL) and returns it as text."""
        if uri.startswith("http://") or uri.startswith("https://"):
            headers = {"User-Agent": "Mozilla/5.0 (ResumeAgent)"}
            try:
                r = requests.get(uri, headers=headers, timeout=10)
                r.raise_for_status()
                # Basic HTML to text, could be improved with BeautifulSoup
                return r.text
            except requests.RequestException as e:
                raise RuntimeError(f"Failed to fetch HTML from {uri}: {e}") from e
        elif pathlib.Path(uri).is_file() and uri.lower().endswith(".pdf"):
            try:
                doc = fitz.open(uri)
                return "\n".join(p.get_text() for p in doc)
            except Exception as e:
                raise RuntimeError(f"Failed to read PDF {uri}: {e}") from e
        else:
            raise ValueError(f"Unsupported URI or file type: {uri}")

@service
class FileStorage:
    """A service for storing files."""
    @tool
    async def save(self, path: str, content: bytes) -> None: ...

@service
class EmbeddingService:
    """A service for generating text embeddings."""
    @tool
    async def embed(self, text: str) -> List[float]: ...

@service
class LLMChat:
    """A service for interacting with a large language model."""
    @tool
    async def chat(self, prompt: str, context: str | None = None) -> str: ...

# --- Agent Tool Definitions --------------------------------------------------

@tool(
    name="read_document",
    description="Read content from a given URI (e.g., a local PDF path or an https:// URL).",
    parameters={
        "type": "object",
        "properties": {
            "uri": {"type": "string", "description": "The URI of the resource to read."},
        },
        "required": ["uri"],
    },
)
async def read_document(uri: str) -> str:
    """Read content from a URI by delegating to the DocumentReader service."""
    reader_svc = await MCP.get(DocumentReader)
    return await reader_svc.read(uri)

@tool(
    name="embed_text",
    description="Generate a vector embedding for a given text.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The text to embed."},
        },
        "required": ["text"],
    },
)
async def embed_text(text: str) -> List[float]:
    """Generate a vector embedding for a text using the EmbeddingService."""
    embedding_svc = await MCP.get(EmbeddingService)
    return await embedding_svc.embed(text)

@tool(
    name="chat_with_llm",
    description="Get a response from the LLM to tailor the resume.",
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "The prompt to send to the LLM."},
            "context": {"type": "string", "description": "Optional context for the prompt, like resume text or a job description."},
        },
        "required": ["prompt"],
    },
)
async def chat_with_llm(prompt: str, context: str | None = None) -> str:
    """Get a response from the LLM using the LLMChat MCP service."""
    llm_chat_svc = await MCP.get(LLMChat)
    return await llm_chat_svc.chat(prompt, context=context)

@tool(
    name="save_tex_file",
    description="Save a .tex file to a specified path.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "The path to save the file to."},
            "content": {"type": "string", "description": "The content of the .tex file."},
        },
        "required": ["path", "content"],
    },
)
async def save_tex_file(path: str, content: str) -> None:
    """Save a .tex file using the FileStorage MCP service."""
    storage_svc = await MCP.get(FileStorage)
    await storage_svc.save(path, content.encode("utf-8"))

@tool(
    name="save_similarity_csv",
    description="Persist similarity rows to a CSV file.",
    parameters={
        "type": "object",
        "properties": {
            "rows": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "job_id":     {"type": "string"},
                        "embed_score":{"type": "number"},
                        "llm_score": {"type": "number"},
                        "company":    {"type": "string"},
                        "url":        {"type": "string"},
                        "title":      {"type": "string"},
                        "posted":     {"type": "string"}
                    },
                    "required": [
                        "job_id","embed_score","llm_score",
                        "company","url","title","posted"
                    ],
                }
            }
        },
        "required": ["rows"],
    },
)
def save_similarity_csv(rows: list[dict]) -> dict:
    content = json.dumps(rows)
    return FileStorage().save(path="results/ranked_jobs.csv", content=content)

@tool(
    name="save_tex_file",
    description="Write a tailored LaTeX résumé to a file.",
    parameters={
        "type": "object",
        "properties": {
            "company": {"type": "string"},
            "title":   {"type": "string"},
            "tex":     {"type": "string"}
        },
        "required": ["company","title","tex"],
    },
)
def save_tex_file(company: str, title: str, tex: str) -> dict:
    path = f"tailored_resumes/{company}/{title}.tex"
    return FileStorage().save(path=path, content=tex)
