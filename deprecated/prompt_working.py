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
    "reason": "Concise explanation of any rejection or score if keep is true."
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

    system_msg = f"""You are an expert resume editor. Your task is to execute a series of commands. You must execute them in order. You must not add any conversational text."""

    user_msg = f"""**JOB DESCRIPTION:**
----------------------------------------------------------
{job_description}
----------------------------------------------------------

**RESUME FILE PATH:**
{resume_path}

**YOUR TASK (execute in this order):**

1.  **FETCH RESUME (DO THIS FIRST):**
    - Call the `fetch_tex_as_text` tool with the path: `{resume_path}`.
    - DO NOT write any text. Call the tool now.
    - If the tool call fails, you must stop and report the error.

2.  **ANALYZE & TAILOR (only after successful fetch):**
    - Analyze the job description for key requirements.
    - Rewrite the fetched resume content to align with the job description.
    - Reorder sections, emphasize relevant skills, and remove irrelevant information.
    - DO NOT add any new information.

3.  **SAVE TAILORED RESUME:**
    - You MUST use the `save_tex` tool to write the tailored LaTeX content.
    - 'save_tex' input: (1) the tailored LaTeX content, (2) the output path.
    - **Output Path:** `tailored_resume/{job_id}.tex`

4.  **CALCULATE FIT SCORE:**
    - Evaluate your tailored resume against the job description.
    - Score from 0.00 to 1.00 based on skill alignment, experience relevance, and keyword optimization.

**OUTPUT FORMAT:**
Return a single JSON object with exactly these keys:

{{
  "success": true/false,
  "score": 0.XX,
  "latex_content": "full tailored LaTeX content",
  "tailoring_summary": "brief description of key changes made",
  "error_message": "error description if success is false, otherwise null"
}}

**ERROR HANDLING:**
- If any step fails, set success to false and provide a reason in `error_message`.
- If the `fetch_tex_as_text` or `save_tex` tool fails, report the error.
"""
    return {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
    }

def updated_resume_tailoring_prompt(row, resume_path):
    """Updated prompt that accounts for the MCP tool return format."""
    job_description = row.get('description', '')
    job_id = row.get('jobid', 'unknown_job')
    output_path = f"tailored_resume/{job_id}/{job_id}.tex"
    system_msg = f"""You are an expert resume editor specializing in tailoring LaTeX resumes for specific job applications.

**AVAILABLE MCP TOOLS:**
- `fetch_tex_as_text(file_path)`: Returns the text content of the file.
- `save_tex(text, output_path)`: Returns 'success' or 'failure'.

**TOOL RESPONSE HANDLING:**
- For fetch_tex_as_text: use the returned text for the actual LaTeX text
- For save_tex: use the returned 'success' or 'failure' for operation success or failure

**TAILORING PROCESS:**
1. Read the original resume using the `fetch_tex_as_text` tool.
2. Tailor the resume based on the given job description.
3. Save the tailored resume using the `save_tex` tool.
4. Calculate the fit score based on the tailored resume and the given job description."""

    user_msg = f"""You must tailor a resume for the following job description:

**<JOB DESCRIPTION>**
{job_description}
**</JOB DESCRIPTION>**

**TASK EXECUTION:**

1. **READ ORIGINAL RESUME**
   ```
   result = fetch_tex_as_text("{resume_path}")
   if result.startswith("failure"):
       return {{"success": false, "error": result, "score": 0.00}}
   
   original_content = result
   ```

2. **TAILOR RESUME**
   - Analyze job requirements/qualifications and map to existing resume content
   - Reorder and emphasize relevant sections
   - MUST keep those skills and experiences relevant to AI/ML.
   - Remove/condense less relevant content, but *never remove any section/section header completely*.
   - Maintain LaTeX formatting
   - Contact information line must be kept in the same line
   - Don't use adjectives like "strong" or "excellent" to describe skills.

3. **SAVE TAILORED RESUME**
   ```
   save_result = save_tex(tailored_content, "{output_path}")
   if save_result.startswith("failure"):
       return {{"success": false, "error": save_result, "score": 0.00}}
   ```

4. **CALCULATE FIT SCORE**
   - Score based on skills alignment, experience relevance, keyword optimization
   - Return float between 0.00-1.00

**OUTPUT FORMAT:**
{{
  "success": true/false,
  "content": "full tailored LaTeX content",
  "error": "error description if success is false, otherwise null",
  "score": 0.XX,
  "saved_path": "path where file was saved"
}}

**ERROR HANDLING EXAMPLES:**
- If read fails: Use the tool's error message directly
- If save fails: Use the tool's error message directly
- Always propagate tool errors to final output

Begin by reading the original resume using the MCP tool."""

    return {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
    }