"""
main.py

Launches the entire ResumeAgent project.

1. Check if collecting urls are required.
    - If need_update, run utils/scrape_linkedin.py and utils/extract_jobposts.py.
    - If no, skip this step.
2. Launch ollama api with qwen3:8b (or other models).    
3. Run main_client.py to launch MCP client.

* Note: Refer to data/ResumeAgent workflow.pdf for the full workflow.
"""

import asyncio
import argparse
import subprocess
import logging
import pandas as pd
import os
from utils.extract_jobposts import ABBREVIATIONS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    """
    Main entry point for the ResumeAgent project.
    Handles starting and stopping the MCP server via stdio.
    """
    parser = argparse.ArgumentParser(description="Run the ResumeAgent project.")
    parser.add_argument("--position", default="Machine Learning Engineer", help="Job position keyword, e.g. 'Machine Learning Engineer'")
    parser.add_argument("--resume-path", default="data/full_resume.tex", help="Path to the LaTeX resume file.")
    parser.add_argument("--job-posts-path", default="outputs/JobPosts.csv", help="Path to the job posts CSV file.")
    parser.add_argument("--need_update", action=argparse.BooleanOptionalAction, default=False, help="Update job posts.")
    args = parser.parse_args()

    try:
        abbr = ABBREVIATIONS.get(args.position.lower())
    except KeyError:
        print(f"Invalid position: {args.position} in ABBREVIATIONS.")
        return
    
    job_posts_path = args.job_posts_path[:-4] + f"_{abbr}.csv"
    filtered_job_posts_path = os.path.dirname(job_posts_path) + f"/Filtered{os.path.basename(job_posts_path)}"
    final_job_posts_path = os.path.dirname(job_posts_path) + f"/Final{os.path.basename(job_posts_path)}"
    tailored_resume_path = os.path.dirname(job_posts_path) + f"/Tailored{os.path.basename(job_posts_path)}"

    if args.need_update:
        logging.info(f"Updating job posts for {args.position}...")
        subprocess.run(["python", "utils/scrape_linkedin.py", "--position", args.position])
        subprocess.run(["python", "utils/extract_jobposts.py", "--position", args.position, "--input", f"outputs/linkedin_outputs_{abbr}.out", "--output", job_posts_path])
    
    logging.info(f"Loading job posts for {args.position}...")
    job_posts = pd.read_csv(job_posts_path)

    """
    Notes: 
    As-is: processes are executed for the entire jobposts in sequence.
    To-do: processes are executed for each jobpost in one iteration.
        - For each job post, if saved in filtered, move on to final filtering, tailor resume, and write tailored resume in pdf.
        - if not saved in filtered or not saved in final, continue to next job post.
    """

    ## TODO: launch ollama api with qwen3:8b
    ## TODO: run main_client.py to launch MCP client
    logging.info(f"Loaded {len(job_posts)} job posts from {job_posts_path}")
    ## The reason we are iterating over df is reading all descriptions at once would 
    # 1. overflow nums of output tokens.
    # 2. take too long to process.
    for idx, row in job_posts.iterrows():
        logging.info(f"Processing job post {idx + 1}/{len(job_posts)}: {row['title']} at {row['company']}")
        ## TODO: deliver row to agent and do filtering & ranking job posts
        ## TODO: Let agent save filtered job posts to FilteredJobPosts_{abbr}.csv

    logging.info(f"Initial screening complete: {filtered_job_posts_path}")
    filtered_job_posts = pd.read_csv(filtered_job_posts_path)
    logging.info(f"Loaded {len(filtered_job_posts)} filtered job posts")
    for idx, row in filtered_job_posts.iterrows():
        logging.info(f"Processing job post {idx + 1}/{len(filtered_job_posts)}: {row['title']} at {row['company']}")
        ## TODO: deliver row to agent and compare resume with job description
        ## TODO: Let agent save final filtered job posts to FinalJobPosts_{abbr}.csv

    logging.info(f"Final screening complete: {final_job_posts_path}")
    final_job_posts = pd.read_csv(final_job_posts_path)
    logging.info(f"Loaded {len(final_job_posts)} final filtered job posts")
    for idx, row in final_job_posts.iterrows():
        logging.info(f"Processing job post {idx + 1}/{len(final_job_posts)}: {row['title']} at {row['company']}")
        ## TODO: deliver row to agent and tailor resume for target job posts
        ## TODO: Let agent save tailored resume to TailoredResume_{abbr}.tex
    
    logging.info(f"Tailoring complete: {final_job_posts_path}")


if __name__ == "__main__":
    asyncio.run(main())
