"""
Agent for tailoring the resume to a specific job description.
"""
from pathlib import Path

import requests
import pdfplumber

import os
import requests
import pdfplumber
from .ollama_utils import ensure_ollama_running

class ResumeTailorAgent:
    def __init__(self, resume_path):
        ensure_ollama_running()
        self.resume_path = resume_path
        self.resume_text = self._extract_text_from_pdf(resume_path)

    def _extract_text_from_pdf(self, pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() or '' for page in pdf.pages)

    def _ollama_generate(self, prompt, model="llama3"):
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False}
        )
        return resp.json()["response"]

    @staticmethod
    def is_url_valid(url: str) -> bool:
        try:
            resp = requests.head(url, allow_redirects=True, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def tailor_resume(self, job: dict):
        company = job.get('company', 'UnknownCompany').replace('/', '_').replace(' ', '_')
        position = job.get('title', 'UnknownPosition').replace('/', '_').replace(' ', '_')
        output_dir = os.path.join('resume', company, position)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'tailored_resume.tex')
        job_desc = job.get('description', '')
        prompt = f"""
You are an expert resume writer. Given the following full resume and a target job description, write a tailored LaTeX (.tex) resume that maximizes the match for this job. Only output valid LaTeX code, no explanations.

Resume:
{self.resume_text}

Target job description:
{job_desc}
"""
        latex_resume = self._ollama_generate(prompt)
        with open(output_path, "w") as out:
            out.write(latex_resume)
        return output_path
