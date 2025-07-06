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
    """
    Build a two‑message array for Ollama / Qwen‑series models.

    Returns
    -------
    dict with shape:
        {
          "messages": [
              {"role": "system", "content": "..."},
              {"role": "user",   "content": "..."}
          ]
        }
    """
    title       = row.get("title", "").strip()
    description = row.get("description", "").strip()

    # Common screening logic reused in both prompts
    screening_block = _screening_logic_block(title, description, position)

    # System prompt – global behaviour instructions
    system_msg = """You are an automated evaluator whose task is to *tightly* assess the similarity between a resume and a job description with maximum rigor and strictness.
You must respond exclusively in valid JSON that matches the required schema, without any extra text, commentary, or formatting.
Any response that does not conform exactly to the schema or contains any additional text is unacceptable."""

    # User prompt – actual task with resume reference
    user_msg = f"""{screening_block}

----------------------------------------------------------
If "keep" is true, you must perform the following additional step:

1. **Resume Scoring**:
   - You **MUST** call the `read_pdf` tool with the following path to get the resume text: `{resume_path}`.
   - You are **NOT** allowed to guess or hallucinate the result of this tool call.
   - If the tool call is successful, use the returned text to score the resume from 0 to 1.
   - If the tool call fails for any reason, set the "score" to 0.

----------------------------------------------------------
Return the same JSON structure as before, but with the "score" field added. If "keep" is false, set "score" to 0.

{{
    "title_pass": true/false,
    "experience_pass": true/false,
    "keep": true/false,
    "score": float,
    "reason": "Concise explanation of any rejection."
}}
"""
    # Keep prompt content but drop the explicit system role; align with
    # the simpler `{ "messages": <str> }` pattern used elsewhere.
    full_prompt = f"{system_msg}{user_msg}"
    return {"messages": full_prompt}
#
# All prompt builders now return an Ollama‑compatible `messages` array including a system message where appropriate.