# Ensure local Ollama server is running before any agent code executes
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

import typer
from pathlib import Path
import asyncio
import subprocess
import sys
import os

from agent_runner import run_resume_agent
# from utils.job_search import JobSearchAgent  # Commented out since we're not using job search

app = typer.Typer(help="A CLI for discovering jobs and tailoring resumes.")


# @app.command()
# def search_jobs(
#     companies_path: Path = typer.Option(
#         Path("data/companies.txt"),
#         exists=True,
#         readable=True,
#         help="Path to a text file with a list of company names.",
#     ),
#     position: str = typer.Option(..., help="Target job title or position to search for."),
#     location: str = typer.Option("California Bay Area", help="Target geographic location."),
#     max_results: int = typer.Option(50, help="Maximum number of jobs to find."),
# ):
#     """Discover job postings and save them to results/job_results.csv."""
#     print("--- Starting Job Search ---")
#     agent = JobSearchAgent(
#         companies_path=companies_path,
#         position=position,
#         location=location,
#         max_results=max_results,
#     )
#     agent.search_jobs()
#     print("--- Job Search Finished ---")


@app.command()
def tailor_resumes(
    jobs_csv_path: Path = typer.Option(
        Path("outputs/JobPosts.csv"),
        exists=True,
        readable=True,
        help="Path to the CSV file containing job listings.",
    ),
    resume_pdf_path: Path = typer.Option(
        Path("data/full_resume.pdf"),
        exists=True,
        readable=True,
        help="Path to your base résumé PDF.",
    ),
    resume_tex_path: Path = typer.Option(
        Path("data/full_resume.tex"),
        exists=True,
        readable=True,
        help="Path to your base résumé TeX file.",
    ),
    max_per_company: int = typer.Option(
        6, 
        help="Maximum number of jobs to keep per company."
    ),
):
    """Tailor your resume for the jobs listed in the CSV file."""
    print("--- Starting Resume Tailoring ---")
    asyncio.run(run_resume_agent(
        jobs_csv_path=jobs_csv_path, 
        resume_pdf_path=resume_pdf_path,
        resume_tex_path=resume_tex_path,
        max_per_company=max_per_company
    ))
    print("--- Resume Tailoring Finished ---")


@app.command()
def launch_mcp(
    background: bool = typer.Option(True, help="Run MCP agent_tools in the background (recommended)."),
):
    """Launch all MCP microservices via agent_tools.py."""
    script_path = os.path.join(os.path.dirname(__file__), "mcp_tools", "agent_tools.py")
    if background:
        subprocess.Popen([sys.executable, script_path])
        print("[MCP] agent_tools.py launched in background.")
    else:
        subprocess.run([sys.executable, script_path])


@app.command()
def check_ollama():
    """Check if Ollama is running and has the required model."""
    try:
        import requests
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            model_names = [model["name"] for model in models.get("models", [])]
            print(f"✓ Ollama is running")
            print(f"✓ Available models: {model_names}")
            
            # Check for qwen models
            qwen_models = [name for name in model_names if "qwen" in name.lower()]
            if qwen_models:
                print(f"✓ Qwen models found: {qwen_models}")
            else:
                print("⚠ No Qwen models found. Run 'ollama pull qwen2.5:latest' or similar.")
        else:
            print("✗ Ollama is not responding properly")
    except Exception as e:
        print(f"✗ Error checking Ollama: {e}")
        print("Make sure Ollama is running: 'ollama serve'")


@app.command()
def setup():
    """Setup the environment and check prerequisites."""
    print("--- Setting up Resume AI Agent ---")
    
    # Check directory structure
    dirs_to_check = ["data", "outputs", "mcp_tools", "tailored_resumes"]
    for dir_name in dirs_to_check:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created directory: {dir_name}")
        else:
            print(f"✓ Directory exists: {dir_name}")
    
    # Check required files
    required_files = [
        "data/full_resume.pdf",
        "data/full_resume.tex",
        "outputs/JobPosts.csv"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✓ File exists: {file_path}")
    
    if missing_files:
        print(f"⚠ Missing files: {missing_files}")
        print("Please ensure these files exist before running the agent.")
    
    # Check Ollama
    print("\n--- Checking Ollama ---")
    check_ollama()
    
    print("\n--- Setup Complete ---")


# --- Optional: Auto-launch MCP tools before agent commands ---
def ensure_mcp_running():
    """Check if MCP tools are running and launch if needed."""
    # Simple check - you might want to implement a more robust check
    import time
    print("Ensuring MCP tools are running...")
    # For now, just give a small delay to let background process start
    time.sleep(2)


if __name__ == "__main__":
    app()