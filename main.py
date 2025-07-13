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
import subprocess
import logging
import pandas as pd
import os
import json
from utils.scrap_linkedin import authenticate_linkedin
from utils.utils import get_score_df, filter_score_df, convert_tex_to_pdf
from resume_agent import ResumeAgent, setup_model_and_tools

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ABBREVIATIONS = {
    'machine learning engineer': "MLE",
    "data scientist": "DS"
}

async def main():
    """
    Main entry point for the ResumeAgent project.
    Handles starting and stopping the MCP server via stdio.
    """

    # Load configuration from JSON file
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Configuration file not found: config.json")
        return
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in configuration file: {e}")
        return
    linkedin_config = config.get("scrap_linkedin")
    try:
        abbr = ABBREVIATIONS.get(config["position"].lower())
        if not abbr:
            print(f"Invalid position: {config['position']} in ABBREVIATIONS.")
            return
    except KeyError:
        print(f"Invalid position: {config['position']} in ABBREVIATIONS.")
        return
    
    # Setup file paths
    job_posts_path = config["job_posts_path"].replace(".csv", f"_{abbr}.csv")
    score_save_path = f"outputs/JobScores_{abbr}.csv"

    # Step 1: Update job posts if needed
    if config["need_update"]:
        logging.info(f"Updating job posts for {config['position']}...")
        linkedin_outputs = f"outputs/linkedin_outputs_{abbr}.out"

        # Load LinkedIn cookie and pass environment to subprocess
        authenticate_linkedin("data/linkedin_cookie.txt")
        env_vars = os.environ.copy()
        
        # Run LinkedIn scraper and capture output
        result = subprocess.run([
            "python", "utils/scrap_linkedin.py", 
            "--position", config["position"], 
            "--num_jobs", str(linkedin_config.get("num_jobs", 10)), 
            "--location", linkedin_config.get("location", "San Jose"), 
            "--filepath", linkedin_config.get("filepath", "data/company_small_list.csv")
        ], capture_output=True, text=True, env=env_vars)
        
        # Save the output to file
        with open(linkedin_outputs, 'w') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write(f"\n# STDERR:\n{result.stderr}")
                
        subprocess.run([
            "python", "utils/extract_jobposts.py", 
            "--position", config["position"], 
            "--input", linkedin_outputs, 
            "--output", job_posts_path
        ])
    
    # Step 2: Setup model and tools
    logging.info(f"Setting up model and MCP tools with {config['api_type']}...")
    model, tools = await setup_model_and_tools(config["api_type"])
    
    # Step 3: Initialize ResumeAgent
    agent = ResumeAgent(model, tools, config["position"], config["resume_path"], config["threshold"])
    
    # Step 4: Load job posts
    logging.info(f"Loading job posts for {config['position']}...")
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
    filter_score_df(score_df, config["threshold"], f"outputs/TargetJobs_{abbr}.csv")
    logging.info(f"Results saved to outputs/TargetJobs_{abbr}.csv")

if __name__ == "__main__":
    asyncio.run(main())
