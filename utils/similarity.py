"""
utils/similarity.py
-------------------
Similarity scoring utilities for ResumeAgent.
- Embedding-based cosine similarity
- LLM-based 0-1 score
"""
import requests
import numpy as np

OLLAMA_HOST = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL   = "llama3:70b-instruct-q5_K_M"  # adjust as needed


def get_embed_score(resume_text: str, jd_text: str) -> float:
    """Compute cosine similarity between resume and job description embeddings."""
    def embed(text: str) -> np.ndarray:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=60,
        )
        resp.raise_for_status()
        return np.array(resp.json()["embedding"])

    r_vec = embed(resume_text)
    j_vec = embed(jd_text)
    score = float(np.dot(r_vec, j_vec) / (np.linalg.norm(r_vec) * np.linalg.norm(j_vec) + 1e-8))
    return score


def get_llm_score(resume_text: str, jd_text: str) -> float:
    """Ask LLM to rate how well resume matches job description (0-1, one decimal)."""
    prompt = (
        "Rate how well the r\u00e9sum\u00e9 matches the job description. "
        "Return only a number 0-1 with one decimal.\n\n"
        f"R\u00c9SUM\u00c9:\n{resume_text[:2000]}\n\n---\n"
        f"JOB DESCRIPTION:\n{jd_text[:2000]}"
    )
    resp = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=90,
    )
    resp.raise_for_status()
    # Extract the number from the LLM response
    import re
    content = resp.json()["message"]["content"]
    m = re.search(r"([01](?:\.\d)?)", content)
    return float(m.group(1)) if m else 0.0
