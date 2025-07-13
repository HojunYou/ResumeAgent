from mcp.server.fastmcp import FastMCP
from aiofiles import open as aopen
from pathlib import Path

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

if __name__ == "__main__":
    mcp.run(transport = 'stdio')
    