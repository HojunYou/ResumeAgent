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
    # 1. Search for jobs
    job_agent = JobSearchAgent(companies_path, position, location, max_results)
    jobs = job_agent.search_jobs()

    # 2. Score jobs by similarity
    ranked_jobs = run_agent(jobs, resume_path)

    print(f"\nFound {len(ranked_jobs)} matching jobs. "
          "Top results ranked by LLM score, then embedding score:\n")

    # 3. Present results and ask user
    for i, job in enumerate(ranked_jobs, 1):
        print(f"{i}. {job['title']} at {job['company']} [{job['url']}] "
              f"(Embed {job['embed_score']:.2f}, LLM {job['llm_score']:.2f})")
    idx = int(input("Select a job to tailor your resume for (0 to exit): "))
    if idx == 0:
        return
    selected_job = ranked_jobs[idx - 1]

    # 4. Check URL validity
    if not ResumeTailorAgent.is_url_valid(selected_job.get('url', '')):
        print(f"[Warning] The job URL {selected_job.get('url', '')} is not valid or reachable. Aborting resume tailoring.")
        return

    # 5. Tailor resume and save in structured directory
    tailor_agent = ResumeTailorAgent(resume_path)
    output_path = tailor_agent.tailor_resume(selected_job)
    print(f"Tailored resume saved to {output_path}")

if __name__ == "__main__":
    app()
