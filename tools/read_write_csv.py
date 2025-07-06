from mcp.server.fastmcp import FastMCP
import csv
import pathlib
from typing import List, Dict, Any

mcp = FastMCP("Read and Write CSV")

@mcp.tool(
    name="read_csv",
    description="Read CSV file."
) #("file://csv/{path}")
def read_csv(path: str) -> dict:
    """Read data from CSV file."""
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
        return {"status":"success", "text":"", "jobs": jobs}
    except Exception as e:
        return {"status":"error", "text": f"Failed to read CSV: {str(e)}"}

@mcp.tool(
    name="write_csv",
    description="Write data to CSV file."
)
def write_csv(jobs: List[dict], output_path: str) -> dict:
    """Write data to CSV file."""
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
        
        return {"status":"success", "text":"", "saved_count": len(jobs)}
        
    except Exception as e:
        return {"status":"error", "text": f"Failed to write CSV: {str(e)}"}

if __name__ == "__main__":
    mcp.run(transport = 'stdio')
