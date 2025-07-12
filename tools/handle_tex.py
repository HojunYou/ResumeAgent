from mcp.server.fastmcp import FastMCP
from aiofiles import open as aopen
from pathlib import Path
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

mcp = FastMCP("Fetch and save LaTeX and convert to PDF")

@mcp.tool(
    # "file://tex/{path}",
    name="fetch_tex_as_text",
    description="Fetch LaTeX resume file content as text."
)
async def fetch_tex_as_text(path: str) -> str:
    try:
        async with aopen(path, 'r', encoding='utf-8') as f:
            return await f.read()
    except Exception as e:
        return f"failure: {str(e)}"

@mcp.tool(
    name="save_latex_resume",
    description="Save LaTeX resume file content as text."
)
async def save_tex(text: str, output_path: str) -> str:
    """Save LaTeX resume file content as text."""
    try:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        async with aopen(output_path, 'w', encoding='utf-8') as f:
            await f.write(text)
        return "success"
    except Exception as e:
        return f"failure: {str(e)}"

@mcp.tool(
    name="convert_tex_to_pdf",
    description="Convert LaTeX resume file to PDF."
)
async def convert_tex_to_pdf(tex_file_path: str, output_dir: str) -> str:
    import subprocess
    import os
    """
    Converts a .tex file to PDF using pdflatex.
    """
    try:
        # Construct the pdflatex command
        command = ["pdflatex", "-output-directory=" + output_dir, tex_file_path]

        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # Print any output or errors
        print("Stdout:", result.stdout)
        print("Stderr:", result.stderr)

        print(f"Successfully converted {tex_file_path} to PDF in {output_dir}")
        return "success"

    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        print("Stdout:", e.stdout)
        print("Stderr:", e.stderr)
        return f"failure: {str(e)}"
    except FileNotFoundError:
        print("pdflatex not found. Make sure LaTeX is installed and in your PATH.")
        return f"failure: pdflatex not found. Make sure LaTeX is installed and in your PATH."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return f"failure: {str(e)}"
if __name__ == "__main__":
    mcp.run(transport = 'stdio')
    