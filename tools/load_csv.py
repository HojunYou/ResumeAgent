from mcp.server.fastmcp import FastMCP
import csv

mcp = FastMCP("Load CSV")

@mcp.resource("file://csv/{path}")
async def load_job_posts(path: str) -> dict:
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

if __name__ == "__main__":
    mcp.run(transport = 'stdio')
