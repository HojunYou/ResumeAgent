import asyncio
import argparse
from agent_runner import run_agent

async def main(resume_path: str, job_posts_path: str, target_jobs_path: str):
    """
    Main entry point for the resume tailoring agent.
    """
    print("Starting Resume Tailoring Agent...")
    await run_agent(resume_path, job_posts_path, target_jobs_path)
    print("Resume Tailoring Agent finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Resume Tailoring Agent.")
    parser.add_argument("--resume-path", default="data/full_resume.tex", help="Path to the LaTeX resume file.")
    parser.add_argument("--job-posts-path", default="outputs/JobPosts.csv", help="Path to the job posts CSV file.")
    parser.add_argument("--target-jobs-path", default="outputs/TargetJobPosts.csv", help="Path to save the target jobs CSV file.")
    args = parser.parse_args()

    try:
        asyncio.run(main(args.resume_path, args.job_posts_path, args.target_jobs_path))
    except KeyboardInterrupt:
        print("\nAgent execution cancelled by user.")
