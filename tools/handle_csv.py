from mcp.server.fastmcp import FastMCP
import csv
import pathlib
from typing import List, Dict, Any

mcp = FastMCP("Load CSV")

@mcp.resource("file://csv/{path}")
def load_csv(path: str) -> dict:
    """Load job postings from JobPosts.csv file."""
    try:
        jobs = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                job = {
                    "job_id": i,
                    "company": row.get("company", ""),
                    "title": row.get("title", ""),
                    "url": row.get("url", ""),
                    "description": row.get("description", ""),
                    "posted": row.get("posted", "")
                }
                jobs.append(job)
        return {"jobs": jobs}
    except Exception as e:
        return {"error": f"Failed to load job posts: {str(e)}"}

@mcp.tool(
    name="save_csv",
    description="Save job postings to CSV file."
)
def save_csv(jobs: List[dict], output_path: str) -> dict:
    """Save job postings to CSV file."""
    try:
        # Ensure output directory exists
        pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = ["job_id", "company", "title", "url", "description", "posted"]
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for job in jobs:
                writer.writerow({
                    "job_id": job["job_id"],
                    "company": job["company"],
                    "title": job["title"],
                    "url": job["url"],
                    "description": job["description"],
                    "posted": job.get("posted", "")
                })
        
        return {"ok": True, "saved_count": len(jobs)}
        
    except Exception as e:
        return {"error": f"Failed to save job posts: {str(e)}"}

if __name__ == "__main__":
    mcp.run(transport = 'stdio')
