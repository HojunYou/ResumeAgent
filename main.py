# Ensure local Ollama server is running before any agent code executes
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

import typer
from pathlib import Path
import asyncio

from agent_runner import run_resume_agent
from utils.job_search import JobSearchAgent

app = typer.Typer(help="A CLI for discovering jobs and tailoring resumes.")


@app.command()
def search_jobs(
    companies_path: Path = typer.Option(
        Path("data/companies.txt"),
        exists=True,
        readable=True,
        help="Path to a text file with a list of company names.",
    ),
    position: str = typer.Option(..., help="Target job title or position to search for."),
    location: str = typer.Option("California Bay Area", help="Target geographic location."),
    max_results: int = typer.Option(50, help="Maximum number of jobs to find."),
):
    """Discover job postings and save them to results/job_results.csv."""
    print("--- Starting Job Search ---")
    agent = JobSearchAgent(
        companies_path=companies_path,
        position=position,
        location=location,
        max_results=max_results,
    )
    agent.search_jobs()
    print("--- Job Search Finished ---")


@app.command()
def tailor_resumes(
    jobs_csv_path: Path = typer.Option(
        Path("results/job_results.csv"),
        exists=True,
        readable=True,
        help="Path to the CSV file containing job listings.",
    ),
    resume_path: Path = typer.Option(
        Path("data/resume.pdf"),
        exists=True,
        readable=True,
        help="Path to your base résumé PDF.",
    ),
):
    """Tailor your resume for the jobs listed in the CSV file."""
    asyncio.run(run_resume_agent(jobs_csv_path, resume_path))


if __name__ == "__main__":
    app()
