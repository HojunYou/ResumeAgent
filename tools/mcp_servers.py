"""
tools.agent_tools
=================
Unified MCP‑compliant toolbox used by the LLM agent for resume tailoring.

Exposed tools
-------------
• fetch_pdf_as_text(path)       → {"text": str}
• fetch_tex_as_text(path)       → {"text": str}
• load_job_posts(csv_path)      → {"jobs": List[dict]}
• compare_resume_job(resume_text, job_desc, company, title) → {"score": float, "analysis": str}
• rank_and_filter_jobs(jobs, scores, max_per_company) → {"filtered_jobs": List[dict]}
• save_target_jobs(jobs, output_path) → {"ok": True}
• tailor_resume_tex(original_tex, job_desc, company, title, job_id) → {"path": str}

Installation: use `uv add "mcp[cli]"` (or `pip install "mcp[cli]"`).
"""

import csv
import pathlib
import re
import json
import aiohttp
import aiofiles
from typing import List, Dict, Any

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP(
    "Resume Tailoring Agent", 
    dependencies=[
        "aiohttp", 
        "aiofiles",
        "fitz",
        "csv",
        "json",
        "pathlib"
    ]
)

# --- Helper Functions --------------------------------------------------------

def _slug(txt: str) -> str:
    """Create a filesystem-safe slug from text."""
    return re.sub(r"[^\w\-]+", "_", txt.lower()).strip("_")

async def call_ollama_api(prompt: str, model: str = "deepseek-r1:8b") -> str:
    """Call Ollama API to get LLM response."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                },
                timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("response", "")
                else:
                    return f"Error: HTTP {response.status}"
    except Exception as e:
        return f"Error calling Ollama API: {str(e)}"

# --- Agent Tool Definitions --------------------------------------------------

@mcp.resource(
    name="fetch_pdf_as_text",
    description="Extract text content from a PDF resume file."
)
async def fetch_pdf_as_text(path: str) -> dict:
    """Extract text from a PDF file using PyMuPDF."""
    try:
        if fitz is None:
            return {"error": "PyMuPDF (fitz) not installed. Run: pip install PyMuPDF"}
        
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return {"text": text}
    except Exception as e:
        return {"error": f"Failed to read PDF: {str(e)}"}

@mcp.resource(
    name="fetch_tex_as_text",
    description="Read LaTeX resume file content as text."
)
async def fetch_tex_as_text(path: str) -> str:
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        return await f.read()

@mcp.tool(
    name="load_job_posts",
    description="Load job postings from CSV file."
)
async def load_job_posts(csv_path: str) -> dict:
    """Load job postings from JobPosts.csv file."""
    try:
        jobs = []
        with open(csv_path, 'r', encoding='utf-8') as f:
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

# @mcp.tool(
#     name="compare_resume_job",
#     description="Compare resume with job description using Ollama LLM API and return score with analysis."
# )
# async def compare_resume_job(resume_text: str, job_desc: str, company: str, title: str) -> dict:
#     """
#     Compare resume with job description using Ollama API.
#     Returns a score (0-100) and detailed analysis.
#     """
#     prompt = f"""
# Analyze how well this resume matches the job description. Focus on:
# 1. Experience years and level match
# 2. Technical skills alignment  
# 3. Qualification requirements
# 4. Industry/domain experience
# 5. Education requirements

# Resume:
# {resume_text}

# Job Description for {title} at {company}:
# {job_desc}

# Provide a JSON response with:
# 1. A numerical score from 0-100 (100 being perfect match)
# 2. Detailed analysis of what matches and what doesn't
# 3. Key missing qualifications or skills
# 4. Strengths that align well

# Format as valid JSON:
# {{
#     "score": <number>,
#     "analysis": "<detailed analysis>",
#     "matches": ["<matching point 1>", "<matching point 2>"],
#     "gaps": ["<missing qualification 1>", "<missing qualification 2>"],
#     "strengths": ["<aligned strength 1>", "<aligned strength 2>"]
# }}
# """
    
#     try:
#         response = await call_ollama_api(prompt)
        
#         # Try to parse JSON response
#         try:
#             # Clean up the response to extract JSON
#             response_clean = response.strip()
#             if response_clean.startswith("```json"):
#                 response_clean = response_clean[7:]
#             if response_clean.endswith("```"):
#                 response_clean = response_clean[:-3]
            
#             result = json.loads(response_clean)
#             return {
#                 "score": result.get("score", 0),
#                 "analysis": result.get("analysis", ""),
#                 "matches": result.get("matches", []),
#                 "gaps": result.get("gaps", []),
#                 "strengths": result.get("strengths", [])
#             }
#         except json.JSONDecodeError:
#             # Fallback if JSON parsing fails
#             return {
#                 "score": 50,  # Default score
#                 "analysis": response,
#                 "matches": [],
#                 "gaps": [],
#                 "strengths": []
#             }
#     except Exception as e:
#         return {
#             "score": 0,
#             "analysis": f"Error during comparison: {str(e)}",
#             "matches": [],
#             "gaps": [],
#             "strengths": []
#         }

# @mcp.tool(
#     name="rank_and_filter_jobs",
#     description="Rank jobs by score and keep top N per company."
# )
# async def rank_and_filter_jobs(jobs: List[dict], scores: List[dict], max_per_company: int = 6) -> dict:
#     """
#     Rank jobs by score and filter to keep top N jobs per company.
#     """
#     try:
#         # Combine jobs with their scores
#         job_scores = []
#         for job, score_data in zip(jobs, scores):
#             job_with_score = {
#                 **job,
#                 "score": score_data.get("score", 0),
#                 "analysis": score_data.get("analysis", ""),
#                 "matches": score_data.get("matches", []),
#                 "gaps": score_data.get("gaps", []),
#                 "strengths": score_data.get("strengths", [])
#             }
#             job_scores.append(job_with_score)
        
#         # Sort by score (descending)
#         job_scores.sort(key=lambda x: x["score"], reverse=True)
        
#         # Filter to keep top N per company
#         company_counts = {}
#         filtered_jobs = []
        
#         for job in job_scores:
#             company = job["company"]
#             if company not in company_counts:
#                 company_counts[company] = 0
            
#             if company_counts[company] < max_per_company:
#                 filtered_jobs.append(job)
#                 company_counts[company] += 1
        
#         return {"filtered_jobs": filtered_jobs}
        
#     except Exception as e:
#         return {"error": f"Failed to rank and filter jobs: {str(e)}"}

# @mcp.tool(
#     name="save_target_jobs",
#     description="Save filtered target jobs to CSV file."
# )
# async def save_target_jobs(jobs: List[dict], output_path: str) -> dict:
#     """Save the filtered and ranked jobs to TargetJobPosts.csv."""
#     try:
#         # Ensure output directory exists
#         pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
#         fieldnames = ["job_id", "score", "company", "title", "url", "description", "posted", "analysis"]
        
#         with open(output_path, "w", newline="", encoding="utf-8") as f:
#             writer = csv.DictWriter(f, fieldnames=fieldnames)
#             writer.writeheader()
#             for job in jobs:
#                 writer.writerow({
#                     "job_id": job["job_id"],
#                     "score": job["score"],
#                     "company": job["company"],
#                     "title": job["title"],
#                     "url": job["url"],
#                     "description": job["description"],
#                     "posted": job.get("posted", ""),
#                     "analysis": job.get("analysis", "")
#                 })
        
#         return {"ok": True, "saved_count": len(jobs)}
        
#     except Exception as e:
#         return {"error": f"Failed to save target jobs: {str(e)}"}

# @mcp.tool(
#     name="tailor_resume_tex",
#     description="Tailor LaTeX resume for specific job and save to specified path."
# )
# async def tailor_resume_tex(original_tex: str, job_desc: str, company: str, title: str, job_id: int) -> dict:
#     """
#     Tailor the LaTeX resume for a specific job posting using Ollama.
#     """
#     prompt = f"""
# Please tailor this LaTeX resume for the following job posting. 
# Make specific modifications to better match the job requirements while keeping the LaTeX structure intact.

# Focus on:
# 1. Adjusting the summary/objective to match the role
# 2. Reordering or emphasizing relevant experience
# 3. Highlighting matching technical skills
# 4. Adjusting project descriptions to align with job requirements
# 5. Keeping all LaTeX formatting and commands intact

# Original LaTeX Resume:
# {original_tex}

# Job Description for {title} at {company}:
# {job_desc}

# Please return ONLY the complete tailored LaTeX resume with all formatting preserved.
# Do not include any explanations or markdown formatting.
# """
    
#     try:
#         tailored_tex = await call_ollama_api(prompt)
        
#         # Save the tailored resume
#         safe_title = _slug(title)
#         safe_company = _slug(company)
        
#         output_path = pathlib.Path(f"tailored_resumes/{safe_company}/{safe_title}_{job_id}.tex")
#         output_path.parent.mkdir(parents=True, exist_ok=True)
        
#         with open(output_path, 'w', encoding='utf-8') as f:
#             f.write(tailored_tex)
        
#         return {"path": str(output_path)}
        
#     except Exception as e:
#         return {"error": f"Failed to tailor resume: {str(e)}"}

# --- Export list -------------------------------------------------------------

__all__ = [
    "fetch_pdf_as_text",
    "fetch_tex_as_text", 
    "load_job_posts",
    "compare_resume_job",
    "rank_and_filter_jobs",
    "save_target_jobs",
    "tailor_resume_tex",
]

if __name__ == "__main__":
    mcp.run()