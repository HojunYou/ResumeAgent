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
"""

import csv, pathlib, re, datetime as dt
from typing import List

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Resume Tailoring Agent")
# --- Agent Tool Definitions --------------------------------------------------

@mcp.tool(
    name="fetch_html",
    description="Download HTML from a URL and return it as plain text.",
    parameters={
        "type": "object",
        "properties": {
            "uri": {"type": "string", "description": "The URI of the resource to read."},
        },
        "required": ["uri"],
    },
)
async def fetch_html(uri: str) -> dict:
    """Download HTML from a URI by delegating to the DocumentReader service."""
    return {"html": requests.get(uri).text}

@mcp.tool(
    name="fetch_pdf_as_text",
    description="Extract text content from a PDF file.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "The path to the PDF file."},
        },
        "required": ["path"],
    },
)
async def fetch_pdf_as_text(path: str) -> dict:
    """Extract text from a PDF file using DocumentReader service."""
    return {"text": fitz.open(path).get_text()}

@mcp.tool(
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
    return await embedding_svc.embed(text)

@mcp.tool(
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

@mcp.tool(
    name="save_result",
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
    description="Save a tailored LaTeX résumé and return its path.",
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
def handle_tex(company: str, title: str, tex: str) -> dict:
    path = pathlib.Path(f"tailored_resumes/{company}/{title}.tex")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tex, encoding="utf-8")
    return {"path": str(path)}

@mcp.tool(
    name="handle_tex",
    description="Save a tailored LaTeX résumé and return its path.",
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
    return handle_tex(company, title, tex)

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