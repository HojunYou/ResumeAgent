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
    Fetch the following LaTeX resume file content as text.
    {path}

    Return the text content in the following format:
    <latex>
    text_content
    </latex>

    For example, if the text content is:
    ```
    \documentclass{{article}}
    \begin{{document}}
    Hello, world!
    \end{{document}}
    ```
    The output should be:
    <latex>
    \documentclass{{article}}
    \begin{{document}}
    Hello, world!
    \end{{document}}
    </latex>

    Do not include any other text.
"""
    return {"messages": prompt}

def fetch_pdf_prompt(path):
    prompt = f"""
    Fetch the following PDF resume file content as text.
    {path}

    Return the text content. No other text."""
    return {"messages": prompt}

def _screening_logic_block(title, description, position):
    system_msg = f"You are an assistant tasked with filtering job postings for a junior-to-mid-level {position} (up to 7 years of experience)."
    user_msg = f"""Here is a job posting:
----------------------------------------------------------
**Title**: {title}

**Job Description**: {description}
----------------------------------------------------------

Perform the following checks and return a JSON object:

1. **Title Check**: Reject if the title includes any of the following words (case-insensitive): 
   'staff', 'principal', 'lead', 'manager', 'infrastructure', 'cuda', or 'researcher'.
   - Exception: Accept if it contains 'technical staff'.

2. **Experience Check**: Reject if the job clearly requires more than 7 years of experience. Do not add required years for different skills.
   - Example: If the job requires 5 years of experience in Python and 5 years of experience in machine learning, pass the job since it requires 5 years of experience.

3. **Skill Check**: 'python' or 'pytorch' must be in the job description.

Output strictly in this format:
{{
  "title_pass": true/false,
  "experience_pass": true/false,
  "skill_pass": true/false,
  "keep": true/false,  // true only if all checks pass
  "reason": "Concise explanation of any rejection."
}}
"""
    # full_prompt = f"{system_msg}\n\n{user_msg}"
    return system_msg, user_msg

def initial_screening_prompt(row, position):
    title = row.get("title", "").strip()
    description = row.get("description", "").strip()
    system_msg, user_msg = _screening_logic_block(title, description, position)
    return {"messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]}

def llm_screening_prompt(row, position, resume_path):
    title = row.get("title", "").strip()
    description = row.get("description", "").strip()

    # Get the detailed screening logic
    screening_system_msg, screening_user_msg = _screening_logic_block(title, description, position)

    # System prompt for the entire multi-step process
    system_msg = f"""{screening_system_msg}

You have a multi-step task:
1.  First, perform the initial screening of the job posting based on the detailed instructions in the user message.
2.  If the screening passes (i.e., "keep" is true), you MUST use the `fetch_pdf_as_text` tool to read the resume at `{resume_path}`. You are not allowed to make up the content of the resume.
3.  After fetching the resume, you will score the similarity between the resume and the job description in scale of 0 to 1 up to 2 decimal places.
    - Put extra focus on, but not limited to, qualifications, education, and skills.
    - Score higher if the resume matches preferred qualifications.
4.  Your final output must be a single JSON object with the keys specified in the user message. If "keep" is false, the "score" should be 0.
"""

    # Add similarity scoring instructions to the user message
    user_msg = f'''{screening_user_msg}

----------------------------------------------------------
If "keep" is true, you must perform the following additional step:

1. **Similarity Scoring**:
   - Fetch the resume text from the path: `{resume_path}`.
   - You are **NOT** allowed to guess or hallucinate the result of this tool call.
   - If the tool call is successful, use the returned text to score similarity between the resume and job description.
   - If the tool call fails for any reason, set the "score" to 0.

----------------------------------------------------------
Your final JSON output must include the "score" field. If "keep" is false, set "score" to 0. The final JSON structure should be:

{{
    "title_pass": true/false,
    "experience_pass": true/false,
    "skill_pass": true/false,
    "keep": true/false,  // true only if all checks pass
    "score": float,
    "reason": "Concise explanation of any rejection."
}}
'''

    return {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
    }

def resume_tailoring_prompt(row, resume_path):
    """
    Generates a prompt for the LLM to tailor a resume.
    The prompt instructs the LLM to first fetch the resume content from a .tex file,
    then tailor it based on the job description.
    """
    job_id = row.get('jobid', 'unknown_job')
    job_description = row.get('description', '')

    system_msg = f"""You are an expert resume editor. Your task is to read a LaTeX resume and rewrite it to match a given job description.

**CORE PRINCIPLES:**
- **NO FABRICATION**: Never invent experiences, skills, or qualifications.
- **TOOL USE IS MANDATORY**: You MUST use the specified tools for fetching and saving the resume.
- **LATEX INTEGRITY**: Maintain the original LaTeX structure and commands.

**PROCESS:**
1.  Fetch the resume content using the `fetch_tex_as_text` tool.
2.  Rewrite the resume to match the job description.
3.  Save the tailored resume using the `save_latex_resume` tool.
4.  Score the fit of the tailored resume.
"""

    user_msg = f"""**JOB DESCRIPTION:**
----------------------------------------------------------
{job_description}
----------------------------------------------------------

**RESUME FILE PATH:**
{resume_path}

**YOUR TASK (execute in this order):**

1.  **FETCH RESUME:**
    - You MUST use the `fetch_tex_as_text` tool to get the content of the resume from the path: `{resume_path}`.
    - You are **NOT** allowed to guess or hallucinate the result of this tool call.
    - If the tool call fails, you must stop and report the error.

2.  **ANALYZE & TAILOR (only after successful fetch):**
    - Analyze the job description for key requirements.
    - Rewrite the fetched resume content to align with the job description.
    - Reorder sections, emphasize relevant skills, and remove irrelevant information.
    - DO NOT add any new information.

3.  **SAVE TAILORED RESUME:**
    - You MUST use the `save_latex_resume` tool to write the tailored LaTeX content.
    - **File Path:** `tailored_resume/{job_id}.tex`

4.  **CALCULATE FIT SCORE:**
    - Evaluate your tailored resume against the job description.
    - Score from 0.00 to 1.00 based on skill alignment, experience relevance, and keyword optimization.

**OUTPUT FORMAT:**
Return a single JSON object with exactly these keys:

{{
  "success": true/false,
  "fit_score": 0.XX,
  "latex_content": "full tailored LaTeX content",
  "tailoring_summary": "brief description of key changes made",
  "error_message": "error description if success is false, otherwise null"
}}

**ERROR HANDLING:**
- If any step fails, set success to false and provide a reason in `error_message`.
- If the `fetch_tex_as_text` or `save_latex_resume` tool fails, report the error.
"""
    return {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
    }
