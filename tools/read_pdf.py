from mcp.server.fastmcp import FastMCP
from aiofiles import open as aiofiles
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

mcp = FastMCP("Fetch PDF")

@mcp.tool(
    # "file://pdf/{path}",
    name="read_pdf",
    description="Extract text content from a PDF resume file."
)
async def read_pdf(path: str) -> dict:
    """Extract text from a PDF file using PyMuPDF."""
    try:
        if fitz is None:
            return {"status":"error", "text": "PyMuPDF (fitz) not installed. Run: uv pip install PyMuPDF"}
        
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return {"status":"success", "text": text}
    except Exception as e:
        return {"status":"error", "text": f"Failed to read PDF: {str(e)}"}

if __name__ == "__main__":
    mcp.run(transport = 'stdio')