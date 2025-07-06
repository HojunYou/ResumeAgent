from mcp.server.fastmcp import FastMCP
from aiofiles import open as aiofiles
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

mcp = FastMCP("Fetch PDF")

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