from mcp.server.fastmcp import FastMCP
from aiofiles import open as aiofiles
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

mcp = FastMCP("Fetch LaTeX and PDF")

@mcp.resource(
    "file://tex/{path}",
    name="fetch_tex_as_text",
    description="Read LaTeX resume file content as text."
)
async def fetch_tex_as_text(path: str) -> str:
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        return await f.read()

@mcp.resource(
    "file://pdf/{path}",
    name="fetch_pdf_as_text",
    description="Extract text content from a PDF resume file."
)
async def fetch_pdf_as_text(path: str) -> dict:
    """Extract text from a PDF file using PyMuPDF."""
    try:
        if fitz is None:
            return {"error": "PyMuPDF (fitz) not installed. Run: uv pip install PyMuPDF"}
        
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return {"text": text}
    except Exception as e:
        return {"error": f"Failed to read PDF: {str(e)}"}


if __name__ == "__main__":
    mcp.run(transport = 'stdio')
    