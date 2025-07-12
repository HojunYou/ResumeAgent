"""
main_client.py

Simple test client for processing individual job postings.
This is used for testing and debugging individual job processing.
"""

import asyncio
import json
import os
import pandas as pd
from typing import Optional

from utils.prompt import llm_screening_prompt, resume_tailoring_prompt
from utils.utils import create_jobID, get_score_df, update_score_df, convert_tex_to_pdf

async def test_single_job(idx: int = 0, resume_path: str = "data/full_resume.pdf", save_path: str = "outputs/JobScores.csv"):
    """
    Test processing a single job posting.
    This function requires the model and tools to be set up externally.
    """
    # Load job data
    job_df = pd.read_csv("outputs/JobPosts.csv")
    if idx >= len(job_df):
        print(f"Index {idx} is out of range. Max index: {len(job_df) - 1}")
        return None
    
    row = job_df.iloc[idx]
    position = "Machine Learning Engineer"
    score_df = get_score_df(job_df, save_path)
    job_id = create_jobID(row, position, idx)
    
    print(f"Testing job {idx}: {row['title']} at {row['company']}")
    print(f"Job ID: {job_id}")
    
    # This function is meant to be called from main.py where model and tools are already set up
    # For now, just return the job information
    return {
        'job_id': job_id,
        'title': row['title'],
        'company': row['company'],
        'description': row['description'][:200] + "..." if len(row['description']) > 200 else row['description']
    }

async def main():
    """Test function for processing a single job."""
    result = await test_single_job(16, "data/full_resume.pdf")
    if result:
        print(f"Job ID: {result['job_id']}")
        print(f"Title: {result['title']}")
        print(f"Company: {result['company']}")
        print(f"Description preview: {result['description']}")
    else:
        print("No job found")

if __name__ == "__main__":
    asyncio.run(main())