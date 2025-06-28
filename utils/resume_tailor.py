"""
agents/resume_tailor_agent.py
=============================

Tailors the résumé *while preserving the exact layout* of `full_resume.pdf`.
Ollama readiness is guaranteed by importing utils.ollama_utils.
"""

from __future__ import annotations
import pathlib, datetime as dt, subprocess, logging, re, textwrap, hashlib
from typing import Dict

import requests
from jinja2 import Template

# ---- side-effect: starts Ollama if it isn't already running
import utils.ollama_utils as _ollama  # noqa: F401  (import for side-effect)

OLLAMA_HOST  = "http://localhost:11434"
CHAT_MODEL   = "llama3:70b-instruct-q5_K_M"   # adjust to local install
TEX_WRAPPER  = r"""
\documentclass[11pt]{article}
\usepackage{geometry}\geometry{margin=0.8in}
\usepackage{hyperref}
\begin{document}
{{ content }}
\end{document}
"""

_LOGGER = logging.getLogger("ResumeTailorAgent")


class ResumeTailorAgent:
    URL_RE = re.compile(r"^https?://", re.I)

    def __init__(self, resume_path: pathlib.Path) -> None:
        self.resume_path = resume_path
        self.base_pdf_bytes = resume_path.read_bytes()
        self.job_template = Template(TEX_WRAPPER)  # compiled once

    # --------------------------------------------------------------------- #
    #                              public                                   #
    # --------------------------------------------------------------------- #
    @staticmethod
    def is_url_valid(url: str, timeout: int = 6) -> bool:
        if not ResumeTailorAgent.URL_RE.match(url):
            return False
        try:
            r = requests.head(url, allow_redirects=True, timeout=timeout)
            return r.status_code < 400
        except requests.RequestException:
            return False

    def tailor_resume(self, job: Dict) -> pathlib.Path:
        """Return path to new .tex file tailored to `job`."""
        prompt = self._build_prompt(job)
        latex_body = self._ollama_chat(prompt)

        today = dt.datetime.utcnow().strftime("%Y%m%d")
        company_dir = pathlib.Path(
            "tailored_resumes", _slug(job["company"])
        )
        company_dir.mkdir(parents=True, exist_ok=True)

        tex_name = f"{_slug(job['title'])}_{job['job_id']}_{today}.tex"
        tex_path = company_dir / tex_name
        tex_path.write_text(latex_body, encoding="utf-8")

        self._compile(tex_path)
        _LOGGER.info("✅ Tailored résumé written → %s", tex_path)
        return tex_path

    # --------------------------------------------------------------------- #
    #                              helpers                                  #
    # --------------------------------------------------------------------- #
    def _build_prompt(self, job: Dict) -> str:
        """
        Instruct the LLM to *mimic* the PDF structure while swapping content.
        We embed the original PDF bytes so the model can infer styling cues.
        """
        jd = job["description"][:1600]  # keep prompt within context limit
        pdf_hex = self.base_pdf_bytes.hex()[:8000]  # partial hex to save tokens

        return textwrap.dedent(
            f"""
            You are a LaTeX résumé re-writer.

            • You are given PARTIAL hex-encoded bytes of the candidate's original résumé
              PDF (`full_resume.pdf`). Use this to preserve visual structure, section
              order, fonts, headings, and overall length **as closely as possible**.

            • Replace *only* the content necessary to maximise alignment with the
              provided job description, while keeping the same look & feel:
              - Keep every existing section header in the same order.
              - Keep the two-column layout (if present), bullet shapes, margins, etc.
              - Do NOT exceed two pages.

            • Return **only** valid LaTeX code between \\begin{{document}} and
              \\end{{document}} – no explanations, no Markdown.

            --- PARTIAL PDF HEX ---
            {pdf_hex}
            --- END PDF HEX ---

            --- JOB DESCRIPTION EXCERPT ---
            {jd}
            --- END JOB DESCRIPTION ---
            """
        ).strip()

    def _ollama_chat(self, prompt: str) -> str:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": CHAT_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=90,
        )
        resp.raise_for_status()
        return self.job_template.render(
            content=resp.json()["message"]["content"]
        )

    @staticmethod
    def _compile(tex_path: pathlib.Path) -> None:
        try:
            subprocess.run(
                ["pdflatex", "-interaction=batchmode", tex_path.name],
                cwd=tex_path.parent,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except subprocess.CalledProcessError:
            _LOGGER.warning("⚠️  pdflatex failed for %s", tex_path.name)


# ------------------------------------------------------------------------- #
#                             util funcs                                    #
# ------------------------------------------------------------------------- #
def _slug(txt: str) -> str:
    return re.sub(r"[^\w\-]+", "_", txt.lower()).strip("_")