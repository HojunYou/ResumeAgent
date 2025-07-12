from mcp.server.fastmcp import FastMCP
from aiofiles import open as aopen
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
    async with aopen(path, 'r', encoding='utf-8') as f:
        return await f.read()

@mcp.tool(
    name="save_latex_resume",
    description="Save LaTeX resume file content as text."
)
async def save_latex_resume(text: str, output_path: str) -> dict:
    """Save LaTeX resume file content as text."""
    try:
        async with aopen(output_path, 'w', encoding='utf-8') as f:
            await f.write(text)
        return {"status": True, "message": "Successfully saved LaTeX file."}
    except Exception as e:
        return {"status": False, "message": f"Failed to save LaTeX file: {str(e)}"}

@mcp.tool(
    name="convert_tex_to_pdf",
    description="Convert LaTeX resume file to PDF."
)
async def convert_tex_to_pdf(tex_file_path: str, output_dir: str) -> None:
    import subprocess
    import os
    """
    Converts a .tex file to PDF using pdflatex.
    """
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Construct the pdflatex command
        command = ["pdflatex", "-output-directory=" + output_dir, tex_file_path]

        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # Print any output or errors
        print("Stdout:", result.stdout)
        print("Stderr:", result.stderr)

        print(f"Successfully converted {tex_file_path} to PDF in {output_dir}")

    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        print("Stdout:", e.stdout)
        print("Stderr:", e.stderr)
    except FileNotFoundError:
        print("pdflatex not found. Make sure LaTeX is installed and in your PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    mcp.run(transport = 'stdio')
    