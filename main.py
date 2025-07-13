"""
main.py

Launches the entire ResumeAgent project.

1. Check if collecting urls are required.
    - If need_update, run utils/scrape_linkedin.py and utils/extract_jobposts.py.
    - If no, skip this step.
2. Launch Chat model and MCP server. (see main_client.py)
3. Call main function in main_client.py to create a client (can I keep it running? so I don't have to launch it every time?)
4. (Optional) serve weekly(or monthly)-updates of job posts.

* Note: Refer to data/ResumeAgent workflow.pdf for the full workflow.
"""

import asyncio
import argparse
import subprocess
import logging
import pandas as pd
import os
from utils.extract_jobposts import ABBREVIATIONS
from utils.utils import get_score_df, filter_score_df, convert_tex_to_pdf
from resume_agent import ResumeAgent, setup_model_and_tools

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def main():
    """
    Main entry point for the ResumeAgent project.
    Handles starting and stopping the MCP server via stdio.
    """
    parser = argparse.ArgumentParser(description="Run the ResumeAgent project.")
    parser.add_argument("--position", default="Machine Learning Engineer", help="Job position keyword, e.g. 'Machine Learning Engineer'")
    parser.add_argument("--resume-path", default="data/full_resume.pdf", help="Path to the LaTeX resume file.")
    parser.add_argument("--job-posts-path", default="outputs/JobPosts.csv", help="Path to the job posts CSV file.")
    parser.add_argument("--need_update", action=argparse.BooleanOptionalAction, default=False, help="Update job posts.")
    parser.add_argument("--threshold", type=float, default=0.6, help="Score threshold for job filtering.")
    parser.add_argument("--num_jobs", type=int, default=10, help="Number of jobs to scrape per company.")
    parser.add_argument("--api_type", type=str, default="openai", help="API type: 'openai' or 'ollama'.")
    args = parser.parse_args()

    try:
        abbr = ABBREVIATIONS.get(args.position.lower())
        if not abbr:
            print(f"Invalid position: {args.position} in ABBREVIATIONS.")
            return
    except KeyError:
        print(f"Invalid position: {args.position} in ABBREVIATIONS.")
        return
    
    # Setup file paths
    job_posts_path = args.job_posts_path.replace(".csv", f"_{abbr}.csv")
    # filtered_job_posts_path = os.path.dirname(job_posts_path) + f"/Filtered{os.path.basename(job_posts_path)}"
    # final_job_posts_path = os.path.dirname(job_posts_path) + f"/Final{os.path.basename(job_posts_path)}"
    # tailored_resume_path = os.path.dirname(job_posts_path) + f"/Tailored{os.path.basename(job_posts_path)}"
    score_save_path = f"outputs/JobScores_{abbr}.csv"

    # Step 1: Update job posts if needed
    if args.need_update:
        logging.info(f"Updating job posts for {args.position}...")
        subprocess.run(["python", "utils/scrape_linkedin.py", "--position", args.position, "--num_jobs", str(args.num_jobs), ">", f"outputs/linkedin_outputs_{abbr}.out"])
        subprocess.run(["python", "utils/extract_jobposts.py", "--position", args.position, "--input", f"outputs/linkedin_outputs_{abbr}.out", "--output", job_posts_path])
    
    # Step 2: Setup model and tools
    logging.info(f"Setting up model and MCP tools with {args.api_type}...")
    model, tools = await setup_model_and_tools(args.api_type)
    
    # Step 3: Initialize ResumeAgent
    agent = ResumeAgent(model, tools, args.position, args.resume_path, args.threshold)
    
    # Step 4: Load job posts
    logging.info(f"Loading job posts for {args.position}...")
    if not os.path.exists(job_posts_path):
        logging.error(f"Job posts file not found: {job_posts_path}")
        return
    
    job_posts = pd.read_csv(job_posts_path)
    score_df = get_score_df(job_posts, score_save_path)
    
    logging.info(f"Loaded {len(job_posts)} job posts from {job_posts_path}")
    
    # Step 5: Process each job posting
    successful_jobs = []
    for idx, row in job_posts.iterrows():
        try:
            result = await agent.process_job_posting(row, idx, score_df, score_save_path)
            ## TODO: check for .tex without .pdf and re-try converting it
            tex_path = result.get('tex_path', '')
            if tex_path and os.path.exists(tex_path) and not os.path.exists(tex_path.replace('.tex', '.pdf')):
                logging.info(f"Re-converting {tex_path} to PDF...")
                try:
                    convert_tex_to_pdf(tex_path, os.path.dirname(tex_path))
                except Exception as e:
                    logging.error(f"Error re-converting {tex_path} to PDF: {e}")
                    continue
            if result['success']:
                successful_jobs.append(result)
        except Exception as e:
            logging.error(f"Error processing job {idx}: {e}")
            continue
    
    # Step 6: Filter and save results
    logging.info(f"Processing complete. {len(successful_jobs)} jobs successfully processed.")
    logging.info(f"Successful jobs:\n{successful_jobs}")
    filter_score_df(score_df, args.threshold, f"outputs/TargetJobs_{abbr}.csv")
    logging.info(f"Results saved to outputs/TargetJobs_{abbr}.csv")

if __name__ == "__main__":
    asyncio.run(main())
