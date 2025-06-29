# ResumeAgent: Automated Resume Tailoring & Job Discovery

ResumeAgent is an AI-powered automation tool that discovers relevant jobs, ranks them by similarity to your resume, and generates tailored resumes for each opportunity. It is designed for robust, extensible, and fully automated operation.

## Features
- **Input:** Full resume (`data/full_resume.pdf`), target companies (`data/company_list.csv`), desired job position(s), and location(s).
- **Automated Career Site Discovery:** Finds each company's official career website and relevant job search page.
- **Job Search & Filtering:** Scrapes jobs from official career sites (supports Greenhouse, Lever, static HTML, and extensible for more). Filters by years of experience, education, posting date, and strict role match.
- **Similarity Scoring:** Uses a local Ollama API for both embedding-based and LLM-based similarity scoring between your resume and each job description.
- **Results Output:** Outputs all selected jobs to `data/job_list.csv` with columns: `JobID`, `SimilarityScore`, `CompanyName`, `CareerWebsite`, `JobDescriptionURL`. Supports up to 6 jobs per company (no artificial filling).
- **Tailored Resume Generation:** For each job, generates a LaTeX `.tex` file in `tailored_resumes/{company}/{position}_{JobID}_{date}.tex`, validated to compile.
- **Weekly Updates & Tracking:** (Planned) Weekly mode checks for new jobs, deduplicates, and generates resumes only for new postings.
- **Robust Logging & Error Handling:** All steps feature robust logging and meaningful error messages.
- **Extensible & Modular:** Easily add new job boards, filters, or AI models.

## Setup & Installation
1. **Prepare Data:**
    - Place your `full_resume.pdf`, `full_resume.tex`, and `company_list.csv` in the `data/` directory.
    - `company_list.csv` should list one company per row.
2. **Install Ollama:**
    - Download from [Ollama](https://ollama.com/download) and ensure `ollama` is in your PATH.
    - Start Ollama with `ollama serve` (ResumeAgent will also try to launch it automatically).
    - Pull required models: for example, `ollama pull nomic-embed-text` and `ollama pull qwen3`.
3. **Install Python Dependencies:**
    - Recommended: [uv](https://github.com/astral-sh/uv) for reproducible environments.
    - Run: `uv pip install -r requirements.txt`
4. **Launch MCP Microservices:**
    - Before running any job search or resume tailoring commands, launch all MCP microservices:
    - `python main.py launch-mcp`
    - (You can add `--background False` to run in the foreground for debugging.)
5. **Run the Agent:**
    - See all options: `python main.py --help`
    - Example: `python main.py search-jobs --position "Machine Learning Engineer" --location "California Bay Area"`
    - Example: `python main.py tailor-resumes --jobs-csv-path results/job_results.csv --resume-path data/resume.pdf`

## Usage
- **First, launch MCP microservices:**
    - `python main.py launch-mcp`
- Then, use the CLI to:
    1. Load company list (`data/company_list.csv`).
    2. Discover career pages and search for jobs matching your criteria.
    3. Rank jobs by similarity to your resume.
    4. Output results to `data/job_list.csv`.
    5. Generate a tailored `.tex` resume for each valid job.
- All tailored resumes are saved in structured directories under `tailored_resumes/`.

### Weekly Update Mode (Planned)
- Run: `python main.py weekly-update ...`
- Checks each company for new jobs, adds only new ones, and generates tailored resumes as needed (no duplicates).

## MCP Microservice Architecture
- All MCP-compliant tools (HTML/PDF fetching, embedding, LLM chat, result saving, LaTeX handling) are exposed via `mcp_tools/agent_tools.py`.
- `agent_tools.py` is the only required launcher for MCP microservices. Launch it via the CLI as shown above.
- Other scripts (including `agent_runner.py`) now assume MCP tools are already running and do not launch microservices themselves.

## Configuration & Extensibility
- **Add New Job Boards:** Extend `JobSearchAgent` with new parsing methods.
- **Change AI Backend:** By default, uses Ollama. To use another local model, update `utils/ollama_utils.py` and scoring logic.
- **Custom Filters:** Modify `_filter_and_rank_jobs` in `job_search.py` for custom filtering logic.
- **Resume Template:** Edit the LaTeX template in `resume_tailor.py` for custom formatting.

## Troubleshooting
- **Ollama Not Running:** Ensure `ollama` is installed, in your PATH, and required models are pulled.
- **Dependency Issues:** Use `uv` for clean environments. See `requirements.txt` for details.
- **.tex Compile Errors:** All generated `.tex` files are validated for compilation. If errors persist, check your LaTeX installation.
- **Logging:** Review logs for detailed error messages and troubleshooting tips.

## Requirements
- See `requirements.txt` for all Python dependencies.
- Requires Python 3.9+.

## Security & Legal
- This project is for demonstration and educational purposes only.
- Web scraping is subject to the terms of service of target sites.
- Do not use your real credentials on third-party sites unless you have permission.

## Contributing & Extending
- Contributions are welcome! See comments and docstrings for extension points.
- To add new job boards or AI models, follow the modular structure in `utils/job_search.py` and `utils/ollama_utils.py`.

---

For any issues or suggestions, please open an issue or PR.

## Example Outputs

### data/job_list.csv
| JobID        | EmbedScore | LLMScore | CompanyName | CareerWebsite                | JobDescriptionURL            |
|--------------|------------|----------|-------------|------------------------------|------------------------------|
| goo_mle_1234 | 0.843      | 0.9      | Google      | https://careers.google.com   | https://.../job/123456       |
| ant_mle_5678 | 0.779      | 0.8      | Anthropic   | https://www.anthropic.com... | https://.../job/654321       |

### Tailored Resume Files
- tailored_resumes/google/machine_learning_engineer_goo_mle_1234_20250628.tex
- tailored_resumes/anthropic/machine_learning_engineer_ant_mle_5678_20250628.tex
