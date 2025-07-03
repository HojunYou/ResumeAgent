"""
SimilarityAgent
===============

Uses Ollama's `/api/embeddings` endpoint (defaults to `mxbai-embed-large`) to
rank job descriptions against your résumé.

The résumé is embedded once at init; each job description is embedded on demand.

Deprecated as no longer needed.
"""
from __future__ import annotations
import pathlib, requests, logging, hashlib
from typing import List, Dict
import pandas as pd
import fitz  # PyMuPDF – lightweight PDF text extraction
import numpy as np

OLLAMA_HOST = "http://localhost:11434"
EMBED_MODEL = "mxbai-embed-large"

class SimilarityAgent:
    def __init__(self, resume_path: pathlib.Path) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.resume_text = self._pdf_to_text(resume_path)
        self.resume_vec  = self._embed(self.resume_text)

    # ----------------- public -----------------

    def rank_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Adds cosine similarity & returns list sorted desc."""
        for j in jobs:
            vec = self._embed(j["description"])
            sim = self._cosine(self.resume_vec, vec)
            j["score"] = round(float(sim), 1)
            j["job_id"] = hashlib.sha1(j["url"].encode()).hexdigest()[:12]

        ranked = sorted(jobs, key=lambda x: x["score"], reverse=True)
        df = pd.DataFrame(ranked)[
            ["job_id", "score", "company", "url", "title", "posted"]
        ]
        pathlib.Path("results").mkdir(exist_ok=True)
        df.to_csv("results/ranked_jobs.csv", index=False)
        self.logger.info("✅ Saved ranked_jobs.csv")

        return ranked

    # ----------------- helpers -----------------

    @staticmethod
    def _pdf_to_text(path: pathlib.Path) -> str:
        doc = fitz.open(path)
        parts = [page.get_text() for page in doc]
        return "\n".join(parts)

    @staticmethod
    def _cosine(v1: list[float], v2: list[float]) -> float:
        a, b = np.array(v1), np.array(v2)
        return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def _embed(self, text: str) -> list[float]:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text[:8000]},
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]