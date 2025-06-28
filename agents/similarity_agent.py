"""
Agent for calculating similarity between resume and job descriptions.
"""
from typing import List, Dict

import requests
import pdfplumber
import numpy as np
from .ollama_utils import ensure_ollama_running

class SimilarityAgent:
    def __init__(self, resume_path):
        ensure_ollama_running()
        self.resume_path = resume_path
        self.resume_text = self._extract_text_from_pdf(resume_path)
        self.resume_emb = self._get_ollama_embedding(self.resume_text)

    def _extract_text_from_pdf(self, pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() or '' for page in pdf.pages)

    def _get_ollama_embedding(self, text):
        resp = requests.post("http://localhost:11434/api/embeddings", json={"model": "nomic-embed-text", "prompt": text})
        return np.array(resp.json()["embedding"])

    def _cosine_similarity(self, a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def rank_jobs(self, jobs: List[Dict]) -> List[Dict]:
        for job in jobs:
            job_text = job.get('description', job.get('title', ''))
            job_emb = self._get_ollama_embedding(job_text)
            job['score'] = self._cosine_similarity(self.resume_emb, job_emb)
        return sorted(jobs, key=lambda x: x['score'], reverse=True)
