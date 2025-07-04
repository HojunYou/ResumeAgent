
"""
agent_runner.py
===============
A script that uses a set of MCP-based tools to rank job descriptions
against a resume and tailor resumes for target jobs.
"""

import asyncio
from mcp.client import Client
import pathlib

async def run_agent(resume_path: str, job_posts_path: str, target_jobs_path: str):
    """
    Main agent loop for tailoring resumes.
    """
    print("--- Starting Resume Tailoring Agent ---")
    
    try:
        async with Client("http://localhost:8000") as mcp:
            # 1. Load job postings
            print(f"Loading job postings from: {job_posts_path}")
            jobs_result = await mcp.load_job_posts(csv_path=job_posts_path)
            if "error" in jobs_result:
                raise Exception(f"Failed to load jobs: {jobs_result['error']}")
            jobs = jobs_result["jobs"]
            print(f"✓ Loaded {len(jobs)} job postings")

            # 2. Load resume content
            print(f"Loading resume from: {resume_path}")
            resume_result = await mcp.fetch_tex_as_text(path=resume_path)
            if "error" in resume_result:
                raise Exception(f"Failed to load resume: {resume_result['error']}")
            resume_tex = resume_result["text"]
            print(f"✓ Loaded TeX resume ({len(resume_tex)} characters)")

            # For comparison, we'll use the text from the TeX resume.
            # If you want to use the PDF text, you can call fetch_pdf_as_text
            resume_text = resume_tex

            # 3. Compare resume against each job
            print(f"Comparing resume against {len(jobs)} job descriptions...")
            scores = []
            for i, job in enumerate(jobs):
                print(f"  [{i+1}/{len(jobs)}] Analyzing: {job['title']} at {job['company']}")
                score = await mcp.compare_resume_job(
                    resume_text=resume_text, 
                    job_desc=job['description'], 
                    company=job['company'], 
                    title=job['title']
                )
                scores.append(score)
                print(f"    Score: {score['score']}")

            # 4. Rank and filter jobs
            print(f"Ranking and filtering jobs...")
            filtered_jobs_result = await mcp.rank_and_filter_jobs(jobs=jobs, scores=scores)
            if "error" in filtered_jobs_result:
                raise Exception(f"Failed to rank and filter jobs: {filtered_jobs_result['error']}")
            filtered_jobs = filtered_jobs_result["filtered_jobs"]
            print(f"✓ Filtered to {len(filtered_jobs)} target jobs")

            # 5. Save target jobs
            print(f"Saving target jobs to: {target_jobs_path}")
            save_result = await mcp.save_target_jobs(jobs=filtered_jobs, output_path=target_jobs_path)
            if "error" in save_result:
                raise Exception(f"Failed to save target jobs: {save_result['error']}")
            print(f"✓ Saved {save_result['saved_count']} target jobs")

            # 6. Generate tailored resumes
            print(f"Generating tailored resumes for {len(filtered_jobs)} jobs...")
            for i, job in enumerate(filtered_jobs):
                print(f"  [{i+1}/{len(filtered_jobs)}] Tailoring for: {job['title']} at {job['company']}")
                tailor_result = await mcp.tailor_resume_tex(
                    original_tex=resume_tex,
                    job_desc=job['description'],
                    company=job['company'],
                    title=job['title'],
                    job_id=job['job_id']
                )
                if "error" in tailor_result:
                    print(f"    ✗ Error: {tailor_result['error']}")
                else:
                    print(f"    ✓ Saved to: {tailor_result['path']}")

            print("\n--- Resume Tailoring Agent Completed Successfully ---")

    except Exception as e:
        print(f"✗ Agent failed: {e}")
        raise

