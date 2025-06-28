"""
tools.agent_tools
=================
Unified MCP‑compliant toolbox used by the LLM agent.

Exposed tools
-------------
• fetch_html(url)            → {"html": str}
• fetch_pdf_as_text(path)    → {"text": str}
• embed_text(text)           → {"vector": [float]}
• save_similarity_csv(rows)  → {"ok": True}
• save_tex_file(company, title, tex) → {"path": str}
"""

from __future__ import annotations
import csv, pathlib, re, datetime as dt
from mcp import tool  # Anthropic MCP decorator
import requests, fitz, json, numpy as np

HEADERS      = {"User-Agent": "ResumeAgent"}
OLLAMA_HOST  = "http://localhost:11434"
EMBED_MODEL  = "mxbai-embed-large"

RESULTS_DIR = pathlib.Path("results")
TEX_DIR     = pathlib.Path("tailored_resumes")

def _slug(text: str) -> str:
    return re.sub(r"[^\w\-]+", "_", text.lower()).strip("_")


# --------------------------------------------------------------------------- #
# Fetch tools
@tool(
    name="fetch_html",
    description="Download raw HTML from a URL.",
    parameters={
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    },
)
def fetch_html(url: str, timeout: int = 10) -> dict:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return {"html": r.text}


@tool(
    name="fetch_pdf_as_text",
    description="Extract plain text from a local PDF file.",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    },
)
def fetch_pdf_as_text(path: str | pathlib.Path) -> dict:
    doc = fitz.open(path)
    return {"text": "\n".join(p.get_text() for p in doc)}


@tool(
    name="embed_text",
    description="Return an embedding vector for the given text using Ollama.",
    parameters={
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    },
)
def embed_text(text: str) -> dict:
    text = text[:8000]  # safety truncation
    resp = requests.post(
        f"{OLLAMA_HOST}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30,
    )
    resp.raise_for_status()
    return {"vector": resp.json()["embedding"]}


@tool(
    name="save_similarity_csv",
    description="Persist similarity rows to results/ranked_jobs.csv.",
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
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / "ranked_jobs.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["job_id", "embed_score", "llm_score",
                        "company", "url", "title", "posted"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return {"ok": True}


@tool(
    name="save_tex_file",
    description="Write a tailored LaTeX résumé to disk and return its path.",
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
    today = dt.datetime.utcnow().strftime("%Y%m%d")
    out_dir = TEX_DIR / _slug(company)
    out_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{_slug(title)}_{today}.tex"
    path = out_dir / file_name
    path.write_text(tex, encoding="utf-8")
    return {"path": str(path)}
