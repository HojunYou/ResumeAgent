"""
agent_runner.py
===============

A script that uses a set of MCP-based tools to rank job descriptions
against a resume and tailor resumes for target jobs.

The agent will:
1. Load job postings from CSV
2. Load resume (PDF and TeX)
3. Compare resume against each job description
4. Rank jobs by match score
5. Filter to top N jobs per company
6. Save target jobs to CSV
7. Generate tailored resumes for each target job
"""

import asyncio
import pathlib
import json
import textwrap
import re
import csv
import aiohttp
from typing import List, Dict, Any

# --- Configuration -----------------------------------------------------------

DEFAULT_RESUME_PDF = pathlib.Path("data/full_resume.pdf")
DEFAULT_RESUME_TEX = pathlib.Path("data/full_resume.tex")
DEFAULT_JOBS_CSV = pathlib.Path("outputs/JobPosts.csv")
TARGET_JOBS_CSV = pathlib.Path("outputs/TargetJobPosts.csv")
TAILORED_RESUMES_DIR = pathlib.Path("tailored_resumes")

# --- Helper Functions --------------------------------------------------------

def _slug(txt: str) -> str:
    """Create a filesystem-safe slug from text."""
    return re.sub(r"[^\w\-]+", "_", txt.lower()).strip("_")

async def call_ollama_api(prompt: str, model: str = "qwen2.5:latest") -> str:
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

async def fetch_pdf_as_text(path: str) -> str:
    """Extract text from PDF file."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        raise Exception(f"Failed to read PDF: {str(e)}")

async def fetch_tex_as_text(path: str) -> str:
    """Read TeX file content."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Failed to read TeX file: {str(e)}")

async def load_job_posts(csv_path: str) -> List[Dict[str, Any]]:
    """Load job postings from CSV file."""
    jobs = []
    try:
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
        return jobs
    except Exception as e:
        raise Exception(f"Failed to load job posts: {str(e)}")

async def compare_resume_job(resume_text: str, job_desc: str, company: str, title: str) -> Dict[str, Any]:
    """Compare resume with job description using Ollama."""
    prompt = f"""
Analyze how well this resume matches the job description. Focus on:
1. Experience years and level match
2. Technical skills alignment  
3. Qualification requirements
4. Industry/domain experience
5. Education requirements

Resume:
{resume_text}

Job Description for {title} at {company}:
{job_desc}

Provide a JSON response with:
1. A numerical score from 0-100 (100 being perfect match)
2. Detailed analysis of what matches and what doesn't
3. Key missing qualifications or skills
4. Strengths that align well

Format as valid JSON:
{{
    "score": <number>,
    "analysis": "<detailed analysis>",
    "matches": ["<matching point 1>", "<matching point 2>"],
    "gaps": ["<missing qualification 1>", "<missing qualification 2>"],
    "strengths": ["<aligned strength 1>", "<aligned strength 2>"]
}}
"""
    
    try:
        response = await call_ollama_api(prompt)
        
        # Try to parse JSON response
        try:
            # Clean up the response to extract JSON
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            
            result = json.loads(response_clean)
            return {
                "score": result.get("score", 0),
                "analysis": result.get("analysis", ""),
                "matches": result.get("matches", []),
                "gaps": result.get("gaps", []),
                "strengths": result.get("strengths", [])
            }
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "score": 50,  # Default score
                "analysis": response,
                "matches": [],
                "gaps": [],
                "strengths": []
            }
    except Exception as e:
        return {
            "score": 0,
            "analysis": f"Error during comparison: {str(e)}",
            "matches": [],
            "gaps": [],
            "strengths": []
        }

async def rank_and_filter_jobs(jobs: List[Dict], scores: List[Dict], max_per_company: int = 6) -> List[Dict]:
    """Rank jobs by score and filter to keep top N per company."""
    # Combine jobs with their scores
    job_scores = []
    for job, score_data in zip(jobs, scores):
        job_with_score = {
            **job,
            "score": score_data.get("score", 0),
            "analysis": score_data.get("analysis", ""),
            "matches": score_data.get("matches", []),
            "gaps": score_data.get("gaps", []),
            "strengths": score_data.get("strengths", [])
        }
        job_scores.append(job_with_score)
    
    # Sort by score (descending)
    job_scores.sort(key=lambda x: x["score"], reverse=True)
    
    # Filter to keep top N per company
    company_counts = {}
    filtered_jobs = []
    
    for job in job_scores:
        company = job["company"]
        if company not in company_counts:
            company_counts[company] = 0
        
        if company_counts[company] < max_per_company:
            filtered_jobs.append(job)
            company_counts[company] += 1
    
    return filtered_jobs

async def save_target_jobs(jobs: List[Dict], output_path: str) -> Dict[str, Any]:
    """Save filtered target jobs to CSV file."""
    try:
        # Ensure output directory exists
        pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = ["job_id", "score", "company", "title", "url", "description", "posted", "analysis"]
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for job in jobs:
                writer.writerow({
                    "job_id": job["job_id"],
                    "score": job["score"],
                    "company": job["company"],
                    "title": job["title"],
                    "url": job["url"],
                    "description": job["description"],
                    "posted": job.get("posted", ""),
                    "analysis": job.get("analysis", "")
                })
        
        return {"ok": True, "saved_count": len(jobs)}
    except Exception as e:
        return {"error": f"Failed to save target jobs: {str(e)}"}

async def tailor_resume_tex(original_tex: str, job_desc: str, company: str, title: str, job_id: int) -> str:
    """Tailor LaTeX resume for specific job using Ollama."""
    prompt = f"""
Please tailor this LaTeX resume for the following job posting. 
Make specific modifications to better match the job requirements while keeping the LaTeX structure intact.

Focus on:
1. Adjusting the summary/objective to match the role
2. Reordering or emphasizing relevant experience
3. Highlighting matching technical skills
4. Adjusting project descriptions to align with job requirements
5. Keeping all LaTeX formatting and commands intact

Original LaTeX Resume:
{original_tex}

Job Description for {title} at {company}:
{job_desc}

Please return ONLY the complete tailored LaTeX resume with all formatting preserved.
Do not include any explanations or markdown formatting.
"""
    
    try:
        tailored_tex = await call_ollama_api(prompt)
        
        # Save the tailored resume
        safe_title = _slug(title)
        safe_company = _slug(company)
        
        output_path = TAILORED_RESUMES_DIR / safe_company / f"{safe_title}_{job_id}.tex"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(tailored_tex)
        
        return str(output_path)
    except Exception as e:
        raise Exception(f"Failed to tailor resume: {str(e)}")

# --- Main Agent Logic --------------------------------------------------------

async def run_resume_agent(
    jobs_csv_path: pathlib.Path = DEFAULT_JOBS_CSV,
    resume_pdf_path: pathlib.Path = DEFAULT_RESUME_PDF,
    resume_tex_path: pathlib.Path = DEFAULT_RESUME_TEX,
    max_per_company: int = 6,
):
    """
    Main agent loop for tailoring resumes.
    
    1. Load job postings from CSV
    2. Load resume (PDF and TeX)
    3. Compare resume against each job description
    4. Rank jobs by match score
    5. Filter to top N jobs per company
    6. Save target jobs to CSV
    7. Generate tailored resumes for each target job
    """
    print("--- Starting Resume Tailoring Agent ---")
    
    try:
        # 1. Load job postings
        print(f"Loading job postings from: {jobs_csv_path}")
        jobs = await load_job_posts(str(jobs_csv_path))
        print(f"✓ Loaded {len(jobs)} job postings")
        
        # 2. Load resume content
        print(f"Loading resume from: {resume_pdf_path}")
        resume_text = await fetch_pdf_as_text(str(resume_pdf_path))
        print(f"✓ Loaded resume text ({len(resume_text)} characters)")
        
        print(f"Loading TeX resume from: {resume_tex_path}")
        resume_tex = await fetch_tex_as_text(str(resume_tex_path))
        print(f"✓ Loaded TeX resume ({len(resume_tex)} characters)")
        
        # 3. Compare resume against each job
        print(f"Comparing resume against {len(jobs)} job descriptions...")
        scores = []
        for i, job in enumerate(jobs):
            print(f"  [{i+1}/{len(jobs)}] Analyzing: {job['title']} at {job['company']}")
            score = await compare_resume_job(
                resume_text, 
                job['description'], 
                job['company'], 
                job['title']
            )
            scores.append(score)
            print(f"    Score: {score['score']}")
        
        # 4. Rank and filter jobs
        print(f"Ranking and filtering jobs (max {max_per_company} per company)...")
        filtered_jobs = await rank_and_filter_jobs(jobs, scores, max_per_company)
        print(f"✓ Filtered to {len(filtered_jobs)} target jobs")
        
        # 5. Save target jobs
        print(f"Saving target jobs to: {TARGET_JOBS_CSV}")
        save_result = await save_target_jobs(filtered_jobs, str(TARGET_JOBS_CSV))
        if save_result.get("ok"):
            print(f"✓ Saved {save_result['saved_count']} target jobs")
        else:
            print(f"✗ Error saving target jobs: {save_result.get('error')}")
        
        # 6. Generate tailored resumes
        print(f"Generating tailored resumes for {len(filtered_jobs)} jobs...")
        for i, job in enumerate(filtered_jobs):
            print(f"  [{i+1}/{len(filtered_jobs)}] Tailoring for: {job['title']} at {job['company']}")
            try:
                tailored_path = await tailor_resume_tex(
                    resume_tex,
                    job['description'],
                    job['company'],
                    job['title'],
                    job['job_id']
                )
                print(f"    ✓ Saved to: {tailored_path}")
            except Exception as e:
                print(f"    ✗ Error: {e}")
        
        print("\n--- Resume Tailoring Agent Completed Successfully ---")
        print(f"Target jobs saved to: {TARGET_JOBS_CSV}")
        print(f"Tailored resumes saved to: {TAILORED_RESUMES_DIR}")
        
    except Exception as e:
        print(f"✗ Agent failed: {e}")
        raise

# --- Entry Point -------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(run_resume_agent())