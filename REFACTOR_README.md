# ResumeAgent Refactored Codebase

## Overview

The ResumeAgent codebase has been refactored to improve organization and maintainability. The main changes are:

1. **Model and Tools moved to `main.py`**: The LLM model and MCP tools are now initialized in `main.py` instead of `main_client.py`
2. **ResumeAgent Class**: A new `ResumeAgent` class encapsulates the job processing logic
3. **Simplified Workflow**: The workflow now processes each job posting in a single iteration through screening and tailoring
4. **Better Error Handling**: Improved error handling and logging throughout the codebase

## File Structure

### Core Files

- **`main.py`**: Main entry point with model/tools setup and complete workflow
- **`resume_agent.py`**: Simplified test client for individual job processing
- **`utils/utils.py`**: Utility functions for job processing and file operations
- **`utils/prompt.py`**: LLM prompts for screening and tailoring
- **`mcp_servers.json`**: MCP server configuration

### Test Files

- **`test_refactor.py`**: Test script to verify the refactored code works correctly

## Key Changes

### 1. Model and Tools Setup

The model and tools are now initialized in `main.py`:

```python
async def setup_model_and_tools() -> tuple[ChatOpenAI, list]:
    """Setup the model and MCP tools."""
    # Load API key and initialize model
    # Load MCP servers and create client
    # Return model and tools
```

### 2. ResumeAgent Class

A new `ResumeAgent` class handles job processing:

```python
class ResumeAgent:
    def __init__(self, model: ChatOpenAI, tools: list, position: str, resume_path: str):
        # Initialize agent with model, tools, and configuration
    
    async def process_job_posting(self, row: pd.Series, idx: Any, score_df: pd.DataFrame, save_path: str) -> Dict[str, Any]:
        # Process a single job posting through screening and tailoring
```

### 3. Simplified Workflow

The workflow now processes each job in a single iteration:

1. **Initial Screening**: Score job based on title, experience, and skills
2. **Resume Tailoring**: For jobs that pass screening, tailor the resume
3. **PDF Generation**: Convert tailored LaTeX to PDF
4. **Score Tracking**: Track both screening and final scores

### 4. Improved Error Handling

- Better exception handling throughout the codebase
- Detailed logging for debugging
- Graceful handling of tool failures

## Usage

### Running the Complete Workflow

```bash
# Basic usage
python main.py

# With custom parameters
python main.py --position "Data Scientist" --resume-path "data/my_resume.pdf" --threshold 0.7

# Update job posts first
python main.py --need_update --position "Machine Learning Engineer"
```

### Testing the Refactored Code

```bash
# Run the test script
python test_refactor.py
```

## Configuration

### MCP Servers

The MCP servers are configured in `mcp_servers.json`:

```json
{
  "mcpServers": {
    "handle_csv": {
      "command": "python",
      "args": ["./tools/read_write_csv.py"],
      "transport": "stdio"
    },
    "handle_tex": {
      "command": "python", 
      "args": ["./tools/handle_tex.py"],
      "transport": "stdio"
    },
    "fetch_pdf_as_text": {
      "command": "python",
      "args": ["./tools/fetch_pdf.py"],
      "transport": "stdio"
    }
  }
}
```

### API Keys

The OpenAI API key should be stored in `~/.openai_key` in the format:

```
"your-api-key-here"
```

## Output Files

The refactored code generates several output files:

- **`outputs/JobScores.csv`**: Contains screening and final scores for all jobs
- **`outputs/TargetJobs.csv`**: Filtered jobs that meet the threshold criteria
- **`tailored_resume/`**: Directory containing tailored resume files

## Benefits of the Refactor

1. **Better Organization**: Model and tools are centralized in `main.py`
2. **Improved Maintainability**: Clear separation of concerns with the `ResumeAgent` class
3. **Enhanced Error Handling**: More robust error handling and logging
4. **Simplified Workflow**: Single iteration processing instead of multiple passes
5. **Better Testing**: Dedicated test script for verification

## Migration Notes

- The old `main_client.py` functionality has been moved to `main.py`
- The workflow now processes jobs in a single pass instead of multiple iterations
- Error handling is more comprehensive
- Logging has been improved for better debugging

## Future Improvements

1. **Parallel Processing**: Process multiple jobs concurrently
2. **Caching**: Cache model responses to avoid reprocessing
3. **Configuration File**: Move hardcoded parameters to a config file
4. **Web Interface**: Add a web interface for easier interaction
5. **Database Integration**: Store results in a database instead of CSV files 