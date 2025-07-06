def load_csv_prompt(csv_path):
    prompt = f"""
    Load job postings from the following CSV file:
    {csv_path}

    Return a list of job dicts. No other text.
    """
    return {"messages": prompt}

def save_csv_prompt(output_path):
    prompt = f"""
    Save job postings to the following CSV file.
    {output_path}
    """
    return {"messages": prompt}

def fetch_tex_prompt(path):
    prompt = f"""
    Read the following LaTeX resume file content as text.
    {path}

    Return the text content. No other text."""
    return {"messages": prompt}

def fetch_pdf_prompt(path):
    prompt = f"""
    Read the following PDF resume file content as text.
    {path}

    Return the text content. No other text."""
    return {"messages": prompt}

def _screening_logic_block(title, description, position):
    return f"""
You are an assistant tasked with filtering job postings for a junior-to-mid-level {position} (up to 7 years of experience).

Here is a job posting:
----------------------------------------------------------
Title: {title}

Job Description:
{description}
----------------------------------------------------------

Perform the following checks and return a JSON object:

1. **Title Check**: Reject if the title includes any of the following words (case-insensitive): 
   'staff', 'principal', 'lead', 'manager', 'infrastructure', 'cuda', or 'researcher'.
   - Exception: Accept if it contains 'technical staff'.

2. **Experience Check**: Reject if the job clearly requires more than 7 years of experience.

Output strictly in this format:
{{
  "title_pass": true/false,
  "experience_pass": true/false,
  "keep": true/false,  // true only if both checks pass
  "reason": "Concise explanation of any rejection."
}}
"""

def initial_screening_prompt(row, position):
    title = row.get("title", "").strip()
    description = row.get("description", "").strip()
    prompt = _screening_logic_block(title, description, position)
    return {"messages": prompt}

def llm_screening_prompt(row, position, resume_path):
    title = row.get("title", "").strip()
    description = row.get("description", "").strip()

    screening = _screening_logic_block(title, description, position)
    
    extended_prompt = f"""{screening}

----------------------------------------------------------
If "keep" is true, additionally perform the following:

Read the following resume file. Then evaluate the relevance and suitability of the resume for this job.

Resume:
{resume_path}

If you cannot read the resume
----------------------------------------------------------
Return the same JSON structure as before, but with one additional field:
  "score": a float between 0 and 1 indicating similarity or match level. If keep is false, set score to 0.

Output format:
{{
  "title_pass": true/false,
  "experience_pass": true/false,
  "keep": true/false,
  "reason": "...",
  "score": float
}}
"""
    return {"messages": extended_prompt}