from mcp.server.fastmcp import FastMCP
from aiofiles import open as aiofiles

mcp = FastMCP("Fetch LaTeX")

@mcp.resource(
    "file://tex/{path}",
    name="fetch_tex_as_text",
    description="Read LaTeX resume file content as text."
)
async def fetch_tex_as_text(path: str) -> str:
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        return await f.read()

if __name__ == "__main__":
    mcp.run(transport = 'stdio')
    