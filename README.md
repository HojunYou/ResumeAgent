# ResumeAgent: Automated Resume Tailoring & Job Discovery

ResumeAgent is an AI-powered automation tool that discovers relevant jobs, ranks them by similarity to your resume, and generates tailored resumes for each opportunity. It is designed for robust, extensible, and fully automated operation.

## Development Status
- Scraping LinkedIn jobs (`utils/scrap_linkedin.py`).
- Debugging `mcp_tools/agent_tools.py`.
- Using OpenAI API (o4-mini model) for LLM-based job screening and resume tailoring.

## Features
- **Input:** Full resume (`data/full_resume.pdf` and `data/full_resume.tex`), target companies (`data/company_list.csv`), desired job position(s), and location(s).
- **Automated Job Posts Discovery:** Each company's linkedin website must be filled in `data/company_list.csv` in `LinkedinURL` column (see `data/company_small_list.csv`). Those companies whose job posts are not appeared on linkedin are not supported as of now. All found jobs (up to `--num-jobs` jobs per company) will be saved to `outputs/JobPosts_{position}.csv`.
- **Job Search & Filtering:** Scrapes jobs from linkedin websites with desired position, location, posting date and etc. Initial filtering by title (`screening_word_list`), years of experience, and key skills.
- **Similarity Scoring:** Uses OpenAI API (o4-mini model) for LLM-based similarity scoring between your resume and each job description. 
    - Ollama apis are also compatible with tool-calling supporting models such as Qwen3 series, but OpenAI models perform better at calling mcp tools in experiments. You can further adjust `resume_tailoring_prompt` in `utils/prompt.py` to improve tool calling with ollama apis.
    - Make sure ollama is installed and your target model is running.
- **Results Output:** Outputs all selected jobs to `outputs/JobScores_{position}.csv` with columns: `jobid`, `score`, `company`, `JobDescriptionURL`, and more.
- **Tailored Resume Generation:** For each job, generates a LaTeX (`{jobid}_{unique_id}.tex`) and a pdf (`{jobid}_{unique_id}.pdf`) file under `tailored_resumes/{company}` directory. Also `final_score` column is added to `outputs/JobScores_{position}.csv` based on the fit of tailored resume to each job description.
- **Weekly Updates & Tracking:** (Planned) Weekly mode checks for new jobs, deduplicates, and generates resumes only for new postings. Only job posts newly updated since the last execution will be updated.
- **Robust Logging & Error Handling:** All steps feature robust logging and meaningful error messages.
- **Extensible & Modular:** Easily add new job boards, filters, or AI models.

## API Costs & Performance
- **Model:** OpenAI o4-mini
- **Cost Estimate:** Less than $0.50 for processing 20 job descriptions (may vary)
- **Processing:** Each job posting requires 2 API calls:
  1. Initial screening (job description analysis)
  2. Resume tailoring (customized resume generation)
- **Efficiency:** Optimized prompts and response parsing for cost-effective operation

## Setup & Installation
1.  **Prepare Data:**
    *   Place your full resume in TeX format at `data/full_resume.tex`.
    *   Create a `data/company_list.csv` file and list the companies you are interested in, one per line. Company name and LinkedinURL must be provided.

2.  **Setup OpenAI API:**
    *   Create an OpenAI API key at [platform.openai.com](https://platform.openai.com/api-keys)
    *   Create a file `~/.openai_key` with your API key in the format: `"your-api-key-here"`
    *   Ensure you have sufficient credits in your OpenAI account

3.  **Install Python Dependencies:**
    *   It is recommended to use a virtual environment.
    *   Install the required packages using `uv` (or `pip`):
        ```bash
        uv pip install -r requirements.txt
        ```

4.  **Run the Application:**
    *   The main script `main.py` now handles starting and stopping all necessary services automatically.
    *   Simply run the agent from your terminal:
        ```bash
        python main.py
        ```
    *   You can also specify custom paths for your files if they differ from the defaults:
        ```bash
        python main.py --resume-path path/to/your/resume.tex --job-posts-path path/to/your/jobs.csv
        ```

## Usage
- The main script `main.py` handles starting and stopping all necessary services automatically.
- Simply run the agent from your terminal:
    ```bash
    python main.py
    ```
- The agent will then:
    1. Load your resume from `data/full_resume.pdf`.
    (Optional) Scrap job posts from Linkedin if `--need_update`.
    2. Load job postings from `outputs/JobPosts_{position}.csv`.
    3. Compare, rank, and filter the jobs using OpenAI API.
    4. Save the top jobs (with a score above a threshold) to `outputs/TargetJobs_{position}.csv`.
    5. Generate tailored LaTeX resumes in the `tailored_resumes/` directory.
- You can customize the file paths using command-line arguments. See `python main.py --help` for more details.

### Weekly Update Mode (Planned)
- Run: `python main.py weekly-update ...`
- Checks each company for new jobs, adds only new ones, and generates tailored resumes as needed (no duplicates).

## Requirements
- See `requirements.txt` for all Python dependencies.
- Tested with Python 3.11+.
- pdflatex must be installed for convertion of .tex to .pdf.
- OpenAI API key and account with sufficient credits.
- (Optional) Ollama must be installed to use ollama-based apis.

## Security & Legal
- This project is for demonstration and educational purposes only.

## Contributing & Extending
- Contributions are welcome! See comments and docstrings for extension points.

### Tailored Resume Files
- tailored_resumes/microsoft/
  - microsoft_mle_0008.tex
  - microsoft_mle_0008.pdf
