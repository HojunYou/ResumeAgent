# Resume Tuning AI Agent

This project is an AI-powered agent that helps you discover and tailor your resume to jobs that best match your profile. It automates job search, similarity scoring, and resume tailoring for positions and locations of your interest.

## Features
- **Input:** Full resume (PDF), target companies list, desired positions/locations.
- **Automated Job Search:** Scrapes LinkedIn and company career pages.
- **Similarity Scoring:** Uses Ollama local VLM API to rank jobs by relevance to your resume.
- **User Interaction:** Presents ranked job URLs, lets you choose to tailor your resume.
- **Job URL Validation:** Checks if the job posting URL is valid before tailoring.
- **Resume Tailoring:** Generates a new `.tex` file for each tailored resume, saved in `resume/company_name/position/tailored_resume.tex`.

## Usage
1. Place your `full_resume.pdf` and `companies.txt` in the `data/` directory.
2. Install [Ollama](https://ollama.com/download) and make sure the `ollama` CLI is available in your PATH.
   - Start Ollama with `ollama serve` (the agent will also try to launch it automatically if not running).
   - Pull required models: `ollama pull nomic-embed-text` and `ollama pull llama3`.
3. Install dependencies with [uv](https://github.com/astral-sh/uv) for fast, reproducible Python environments:
   - `uv pip install -r requirements.txt`
4. Run `python main.py --help` for options.

## How it works
- The agent fetches job descriptions directly from the provided URLs and parses the main content for similarity scoring and tailoring.

## Troubleshooting
- If you see errors about Ollama not running or not installed, follow the installation instructions above and ensure the CLI is in your PATH.
- For best results, ensure the required models are pulled before running the agent.

## Requirements
See `requirements.txt`.

---

This project is for demonstration and educational purposes only. Web scraping is subject to the terms of service of target sites.
