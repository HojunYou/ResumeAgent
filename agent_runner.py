"""
agent_runner.py
===============

A script that uses a set of MCP-based tools to rank job descriptions
against a resume.

The agent will:

• iterate over a list of job URLs
"""

from __future__ import annotations
import asyncio
import pathlib
import json
import textwrap
import re
import pandas as pd

from mcp import bootstrap
from tools import agent_tools

# --- Configuration -----------------------------------------------------------

DEFAULT_RESUME_PDF = pathlib.Path("data/resume.pdf")
DEFAULT_JOBS_CSV = pathlib.Path("results/job_results.csv")
TAILORED_RESUMES_DIR = pathlib.Path("tailored_resumes")

# --- Helper Functions --------------------------------------------------------

def _slug(txt: str) -> str:
    return re.sub(r"[^\w\-]+", "_", txt.lower()).strip("_")

def _build_prompt(resume_text: str, job_description: str) -> str:
    """
    Builds the prompt for the LLM to rewrite the resume.
    """
    return textwrap.dedent(
        f"""
        You are a LaTeX résumé re-writer.

        Your task is to tailor the provided résumé to maximize its alignment with the given job description.
        You must preserve the original resume's structure, section order, and overall formatting as much as possible.
        Replace content where necessary to highlight relevant skills and experiences, but maintain the original's voice and style.

        Return **only** the full, valid LaTeX document content. Do not include any explanations or markdown formatting.

        --- ORIGINAL RÉSUMÉ TEXT ---
        {resume_text}
        --- END RÉSUMÉ TEXT ---

        --- JOB DESCRIPTION ---
        {job_description}
        --- END JOB DESCRIPTION ---
        """
    ).strip()

# --- Main Agent Logic --------------------------------------------------------

async def run_resume_agent(
    jobs_csv_path: pathlib.Path = DEFAULT_JOBS_CSV,
    resume_pdf_path: pathlib.Path = DEFAULT_RESUME_PDF,
):
    """
    Main agent loop for tailoring resumes.

    1.  Load MCP services from config.
    2.  Read the base resume text.
    3.  Read the list of jobs from the CSV.
    4.  For each job, read the JD, generate a tailored resume via LLM, and save it.
    """
    print("--- Starting Resume Tailoring Agent ---")

    # 1. Bootstrap MCP services
    try:
        with open("mcp_config.json") as f:
            config = json.load(f)
        await bootstrap.from_config(config)
        print("MCP services bootstrapped successfully.")
    except FileNotFoundError:
        print("mcp_config.json not found. Cannot bootstrap MCP services.")
        return
    except Exception as e:
        print(f"Error bootstrapping MCP services: {e}")
        return

    # 2. Read base resume text
    try:
        print(f"Reading base resume from: {resume_pdf_path}")
        resume_text = await agent_tools.read_document(str(resume_pdf_path))
    except Exception as e:
        print(f"Error reading resume PDF: {e}")
        return

    # 3. Read jobs from CSV
    try:
        jobs_df = pd.read_csv(jobs_csv_path)
        print(f"Found {len(jobs_df)} jobs to process from {jobs_csv_path}.")
    except FileNotFoundError:
        print(f"Jobs CSV not found at {jobs_csv_path}. Run the job search first.")
        return

    # 4. Process each job
    for _, job in jobs_df.iterrows():
        job_id = job.get("JobID", "unknown_job")
        company = job.get("CompanyName", "unknown_company")
        title = job.get("JobTitle", "unknown_title")
        url = job.get("JobDescriptionURL")

        print(f"\nProcessing job: {title} at {company} ({job_id})")

        if not url or not isinstance(url, str):
            print("  -> Skipping job due to missing or invalid URL.")
            continue

        try:
            # 4.1. Read job description
            print(f"  -> Reading job description from: {url}")
            jd_text = await agent_tools.read_document(url)

            # 4.2. Generate tailored resume via LLM
            print("  -> Generating tailored resume with LLM...")
            prompt = _build_prompt(resume_text, jd_text)
            tailored_resume_tex = await agent_tools.chat_with_llm(prompt)

            # 4.3. Save the tailored .tex file
            company_dir = TAILORED_RESUMES_DIR / _slug(company)
            company_dir.mkdir(parents=True, exist_ok=True)
            tex_name = f"{_slug(title)}_{job_id}.tex"
            tex_path = company_dir / tex_name

            print(f"  -> Saving tailored resume to: {tex_path}")
            await agent_tools.save_tex_file(str(tex_path), tailored_resume_tex)
            print(f"  Successfully tailored resume for {job_id}.")

        except Exception as e:
            print(f"  Failed to process job {job_id}: {e}")

    print("\n--- Resume Tailoring Agent Finished ---")

# --- Entry Point -------------------------------------------------------------

if __name__ == "__main__":
    # This script now only runs the resume tailoring part.
    # The job search should be run separately.
    asyncio.run(run_resume_agent())