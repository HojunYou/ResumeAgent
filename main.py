import asyncio
import argparse
import subprocess
import time
import sys
from agent_runner import run_agent

async def main():
    """
    Main entry point for the resume tailoring agent.
    Handles starting and stopping the MCP server.
    """
    parser = argparse.ArgumentParser(description="Run the Resume Tailoring Agent.")
    parser.add_argument("--resume-path", default="data/full_resume.tex", help="Path to the LaTeX resume file.")
    parser.add_argument("--job-posts-path", default="outputs/JobPosts.csv", help="Path to the job posts CSV file.")
    parser.add_argument("--target-jobs-path", default="outputs/TargetJobPosts.csv", help="Path to save the target jobs CSV file.")
    args = parser.parse_args()

    # Command to run the MCP server
    # Using sys.executable ensures we use the same python interpreter
    server_command = [sys.executable, "-m", "mcp_tools.agent_tools"]
    server_process = None

    try:
        # Start the MCP server in the background
        print("--- Starting MCP server in the background... ---")
        server_process = subprocess.Popen(server_command)
        
        # Give the server a moment to initialize
        print("--- Waiting for server to initialize (5 seconds)... ---")
        time.sleep(5)
        
        # Check if the server started successfully
        if server_process.poll() is not None:
            print("✗ Error: MCP server failed to start. Please check for errors.")
            return

        print("\n--- Server started. Running the agent... ---")
        await run_agent(args.resume_path, args.job_posts_path, args.target_jobs_path)

    except KeyboardInterrupt:
        print("\nAgent execution cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if server_process and server_process.poll() is None:
            print("\n--- Shutting down MCP server... ---")
            server_process.terminate()
            server_process.wait()
            print("--- Server shut down. ---")
    
    print("Resume Tailoring Agent finished.")

if __name__ == "__main__":
    asyncio.run(main())