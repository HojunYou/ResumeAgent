"""
ResumeTailorAgent
=================

• Validates job URLs (HEAD request).
• Calls Ollama’s chat endpoint with a prompt that returns LaTeX content.
• Saves `.tex` in a tidy directory structure and optionally compiles to PDF.
"""
from __future__ import annotations
import pathlib, requests, logging, datetime as dt, subprocess, re, shutil, hashlib, textwrap
from typing import Dict
from jinja2 import Template

OLLAMA_HOST  = "http://localhost:11434"
CHAT_MODEL   = "llama3:70b-instruct-q5_K_M"   # adjust to your local model name
TEX_TEMPLATE = r"""
\documentclass[11pt]{article}
\usepackage{geometry}\geometry{margin=0.8in}
\usepackage{hyperref}
\begin{document}
{{ content }}
\end{document}
"""

class ResumeTailorAgent:
    URL_RE = re.compile(r"^https?://")

    def __init__(self, resume_path: pathlib.Path) -> None:
        self.resume_path = resume_path
        self.logger      = logging.getLogger(self.__class__.__name__)
        self.base_text   = resume_path.read_text() if resume_path.suffix == ".tex" else ""
        # If PDF, SimilarityAgent already extracted; we just send file bytes here if needed.

    # ----------------- public -----------------

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
        """Returns path to the new .tex file."""
        prompt = self._build_prompt(job)
        latex_body = self._ollama_chat(prompt)

        today = dt.datetime.utcnow().strftime("%Y%m%d")
        company_dir = pathlib.Path("tailored_resumes", _slug(job["company"]))
        company_dir.mkdir(parents=True, exist_ok=True)

        outfile = company_dir / f"{_slug(job['title'])}_{job['job_id']}_{today}.tex"
        outfile.write_text(latex_body, encoding="utf-8")

        # Quick sanity compile; errors → logs
        self._compile_tex(outfile)

        self.logger.info("✅ Tailored résumé saved → %s", outfile)
        return outfile

    # ----------------- helpers -----------------

    def _build_prompt(self, job: Dict) -> str:
        jd_excerpt = job["description"][:1500]  # keep prompt short
        return textwrap.dedent(
            f"""
            You are a résumé-writing assistant. Given the candidate résumé below and
            the job description, produce a concise LaTeX résumé (<= 2 pages) that
            highlights the most relevant experiences for the role.

            Candidate résumé (raw text):
            ----
            {self.base_text}
            ----

            Job description excerpt:
            ----
            {jd_excerpt}
            ----

            Return *only* valid LaTeX content inside \\begin{{document}}...\\end{{document}}.
            """
        )

    def _ollama_chat(self, prompt: str) -> str:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": CHAT_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=60,
        )
        resp.raise_for_status()
        content = resp.json()["message"]["content"]

        # wrap inside mini template to guarantee compile
        template = Template(TEX_TEMPLATE)
        return template.render(content=content)

    def _compile_tex(self, tex_path: pathlib.Path) -> None:
        try:
            subprocess.run(
                ["pdflatex", "-interaction=batchmode", tex_path.name],
                cwd=tex_path.parent,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except subprocess.CalledProcessError:
            self.logger.warning("⚠️  pdflatex failed for %s", tex_path.name)

# --------------- utilities -------------------

def _slug(text: str) -> str:
    return re.sub(r"[^\w\-]+", "_", text.lower()).strip("_")