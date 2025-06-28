# Ensure local Ollama server is running before any agent code executes
import utils.ollama_utils  # side‑effect: ensure_ollama_running()
import logging
logging.basicConfig(level=logging.INFO,
                    format="%(levelname)s | %(name)s | %(message)s")
import typer
from agent_runner import run_agent
from utils.job_search import JobSearchAgent
from utils.resume_tailor import ResumeTailorAgent
from pathlib import Path

app = typer.Typer()

@app.command()
def run(
    resume_path: Path = typer.Option(
        Path("data/full_resume.pdf"), exists=True, readable=True,
        help="Path to your full résumé PDF"
    ),
    companies_path: Path = typer.Option(
        Path("data/companies.txt"), exists=True, readable=True,
        help="Path to companies.txt file"
    ),
    position: str = typer.Option(..., help="Target job title or position"),
    location: str = typer.Option(..., help="Target location(s), comma separated"),
    max_results: int = typer.Option(50, help="Maximum number of job results to fetch")
):
    """Main entrypoint for the Resume Tuning Agent."""
    import logging
    logger = logging.getLogger("main")
    # 1. Search for jobs
    job_agent = JobSearchAgent(companies_path, position, location, max_results)
    jobs = job_agent.search_jobs()

    # 2. Score jobs by similarity
    ranked_jobs = run_agent(jobs, resume_path)

    print(f"\nFound {len(ranked_jobs)} matching jobs. "
          "Top results ranked by LLM score, then embedding score:\n")
    for i, job in enumerate(ranked_jobs, 1):
        print(f"{i}. {job.get('title','')} at {job.get('company','')} [{job.get('url','')}] "
              f"(Embed {job.get('embed_score',0):.2f}, LLM {job.get('llm_score',0):.2f})")

    # 3. Tailor resumes for all valid jobs
    tailor_agent = ResumeTailorAgent(resume_path)
    for job in ranked_jobs:
        url = job.get('url', '')
        if not ResumeTailorAgent.is_url_valid(url):
            logger.warning(f"[Warning] The job URL {url} is not valid or reachable. Skipping resume tailoring.")
            continue
        try:
            output_path = tailor_agent.tailor_resume(job)
            print(f"Tailored resume saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to tailor resume for job {job.get('job_id','')}: {e}")

@app.command()
def weekly_update(
    resume_path: Path = typer.Option(
        Path("data/full_resume.pdf"), exists=True, readable=True,
        help="Path to your full résumé PDF"
    ),
    companies_path: Path = typer.Option(
        Path("data/companies.txt"), exists=True, readable=True,
        help="Path to companies.txt file"
    ),
    position: str = typer.Option(..., help="Target job title or position"),
    location: str = typer.Option(..., help="Target location(s), comma separated"),
    max_results: int = typer.Option(50, help="Maximum number of job results to fetch")
):
    """
    Weekly update: checks for new postings, deduplicates, and generates tailored resumes as needed.
    (Stub implementation: to be filled in with tracking logic.)
    """
    print("[Weekly update mode is not yet fully implemented.]")
    # TODO: Implement tracking of previously processed jobs and only process new ones.

if __name__ == "__main__":
    app()
