# Resume AI Agent - Execution Guide

## Key Fixes Made to `agent_tools.py`

### 1. **Fixed Import Issues**
- Added proper error handling for PyMuPDF import
- Moved `aiohttp` import to top level
- Added missing `json` import

### 2. **Fixed Function Signatures**
- Updated `compare_resume_job` to use the same logic as `agent_runner.py`
- Improved JSON parsing with better error handling
- Added proper response cleaning for JSON extraction

### 3. **Fixed Helper Functions**
- Moved `call_ollama_api` and `_slug` functions to module level
- Unified the Ollama API calling logic between files
- Added proper timeout handling

### 4. **Fixed File Path Handling**
- Updated `tailor_resume_tex` to use proper path construction
- Added better error handling for file operations

## How to Execute `main.py`

### Prerequisites Setup

1. **Install Ollama and pull a model:**
   ```bash
   # Install Ollama (visit https://ollama.ai for installation)
   ollama pull qwen2.5:latest
   ollama serve  # Start the server
   ```

2. **Check if everything is working:**
   ```bash
   python main.py check-ollama
   ```

3. **Setup project structure:**
   ```bash
   python main.py setup
   ```

### Running the Application

1. **Basic usage - tailor resumes:**
   ```bash
   python main.py tailor-resumes
   ```

2. **With custom parameters:**
   ```bash
   python main.py tailor-resumes \
     --jobs-csv-path outputs/JobPosts.csv \
     --resume-pdf-path data/full_resume.pdf \
     --resume-tex-path data/full_resume.tex \
     --max-per-company 6
   ```

3. **Get help:**
   ```bash
   python main.py --help
   python main.py tailor-resumes --help
   ```

### Required File Structure

Before running, ensure you have:
```
project/
├── main.py
├── agent_runner.py
├── mcp_tools/
│   └── agent_tools.py
├── data/
│   ├── full_resume.pdf
│   └── full_resume.tex
├── outputs/
│   └── JobPosts.csv
└── tailored_resumes/  # Will be created automatically
```

## Requirements.txt

```txt
# Core dependencies
typer>=0.9.0
aiohttp>=3.8.0
PyMuPDF>=1.23.0
pathlib>=1.0.0

# MCP framework
mcp[cli]>=0.1.0

# Optional but recommended
uvloop>=0.17.0  # For better async performance on Linux/macOS
```

## Environment Setup Commands

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or using uv (faster)
uv pip install -r requirements.txt
```

## Troubleshooting

### Common Issues:

1. **Ollama not running:**
   ```bash
   ollama serve
   ```

2. **Missing model:**
   ```bash
   ollama pull qwen2.5:latest
   ```

3. **Permission errors:**
   ```bash
   chmod +x main.py
   ```

4. **Missing files:**
   - Ensure `JobPosts.csv` exists in `outputs/`
   - Ensure `full_resume.pdf` and `full_resume.tex` exist in `data/`

### Expected Workflow:

1. **Setup:** `python main.py setup`
2. **Check:** `python main.py check-ollama`
3. **Run:** `python main.py tailor-resumes`
4. **Results:** Check `outputs/TargetJobPosts.csv` and `tailored_resumes/`

The application will:
- Load job postings from CSV
- Analyze your resume against each job
- Score and rank jobs by fit
- Filter to top N jobs per company
- Generate tailored LaTeX resumes for each target job
- Save results to CSV and individual `.tex` files