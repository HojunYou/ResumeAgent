import asyncio
import argparse
from mcp_core.mcp_client import run_agent
from mcp import StdioServerParameters

async def main():
    """
    Main entry point for the resume tailoring agent.
    Handles starting and stopping the MCP server via stdio.
    """
    parser = argparse.ArgumentParser(description="Run the Resume Tailoring Agent.")
    parser.add_argument("--resume-path", default="data/full_resume.tex", help="Path to the LaTeX resume file.")
    parser.add_argument("--job-posts-path", default="outputs/JobPosts.csv", help="Path to the job posts CSV file.")
    parser.add_argument("--target-jobs-path", default="outputs/TargetJobPosts.csv", help="Path to save the target jobs CSV file.")
    args = parser.parse_args()

    # StdioServerParameters to run the MCP server script
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "--active", "mcp", "dev", "mcp_core/mcp_servers.py"],
        env=None,
    )

    try:
        print("--- Running agent and server via stdio... ---")
        # The agent runner will now manage the server process
        await run_agent(server_params, args.resume_path, args.job_posts_path, args.target_jobs_path)

    except KeyboardInterrupt:
        print("\nAgent execution cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    print("Resume Tailoring Agent finished.")

if __name__ == "__main__":
    asyncio.run(main())
