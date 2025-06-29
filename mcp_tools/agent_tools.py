"""
tools.agent_tools
=================
Unified MCP‑compliant toolbox used by the LLM agent.

Exposed tools
-------------
• fetch_html(uri)               → {"html": str}
• fetch_pdf_as_text(path)       → {"text": str}
• embed_text(text)              → {"vector": [float]}
• chat_with_llm(prompt, ctx)    → {"message": str}
• save_result(rows)             → {"ok": True}
• handle_tex(company,title,tex) → {"path": str}

Installation: use `uv add "mcp[cli]"` (or `pip install "mcp[cli]"`).
"""

import csv, pathlib, re
import datetime as dt
from typing import List
import requests, fitz  # external deps used in tools

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Resume Tailoring Agent")
# --- Agent Tool Definitions --------------------------------------------------

@mcp.tool(
    name="fetch_html",
    description="Download HTML from a URL and return it as plain text."
)
async def fetch_html(uri: str) -> dict:
    """Download HTML from a URI by delegating to the DocumentReader service."""
    return {"html": requests.get(uri).text}

@mcp.tool(
    name="fetch_pdf_as_text",
    description="Extract text content from a PDF file."
)
async def fetch_pdf_as_text(path: str) -> dict:
    """Extract text from a PDF file using DocumentReader service."""
    return {"text": fitz.open(path).get_text()}

@mcp.tool(
    name="embed_text",
    description="Generate a vector embedding for a given text."
)
async def embed_text(text: str) -> List[float]:
    """Generate a vector embedding for a text using the EmbeddingService."""
    return await embedding_svc.embed(text)

@mcp.tool(
    name="chat_with_llm",
    description="Get a response from the LLM to tailor the resume."
)
async def chat_with_llm(prompt: str, context: str | None = None) -> str:
    """Get a response from the LLM using the LLMChat MCP service."""
    llm_chat_svc = await MCP.get(LLMChat)
    return await llm_chat_svc.chat(prompt, context=context)

@mcp.tool(
    name="save_result",
    description="Persist similarity rows to a CSV file."
)
def save_result(rows: list[dict]) -> dict:
    fieldnames = ["job_id","embed_score","llm_score","company","url","title","posted"]
    pathlib.Path("results").mkdir(parents=True, exist_ok=True)
    with open("results/ranked_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return {"ok": True}

@mcp.tool(
    name="handle_tex",
    description="Save a tailored LaTeX résumé and return its path."
)
def handle_tex(company: str, title: str, tex: str) -> dict:
    path = pathlib.Path(f"tailored_resumes/{company}/{title}.tex")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tex, encoding="utf-8")
    return {"path": str(path)}

__all__ = [
    "fetch_html",
    "fetch_pdf_as_text",
    "embed_text",
    "chat_with_llm",
    "save_result",
    "handle_tex",
]

if __name__ == "__main__":
    mcp.run()