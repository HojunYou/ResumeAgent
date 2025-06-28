"""
tools.mcp  –  Mini “MCP server” wrappers (side-effect helpers).

• save_similarity_csv(rows: list[dict]) -> None
• save_tex_file(company, title, tex)    -> pathlib.Path
"""

from __future__ import annotations
import csv, pathlib, re, datetime as dt

RESULTS_DIR = pathlib.Path("results")
TEX_DIR     = pathlib.Path("tailored_resumes")

def _slug(text: str) -> str:
    return re.sub(r"[^\w\-]+", "_", text.lower()).strip("_")


def save_similarity_csv(rows: list[dict]) -> None:
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


def save_tex_file(company: str, title: str, tex: str) -> pathlib.Path:
    today = dt.datetime.utcnow().strftime("%Y%m%d")
    out_dir = TEX_DIR / _slug(company)
    out_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{_slug(title)}_{today}.tex"
    path = out_dir / file_name
    path.write_text(tex, encoding="utf-8")
    return path

# --------------------------------------------------------------------------- #
def fetch_html(url: str, timeout: int = 10) -> str:
    """Return raw HTML (or raise requests.HTTPError)."""
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text


def fetch_pdf_as_text(path: str | pathlib.Path) -> str:
    """Return plain text extracted from a PDF file."""
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)