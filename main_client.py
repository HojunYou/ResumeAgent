from langchain_mcp_adapters.client import MultiServerMCPClient, load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
import asyncio
import json

from utils.prompts import load_csv_prompt, fetch_tex_prompt, fetch_pdf_prompt

async def main():
    model = ChatOllama(model="qwen3:8b")
    servers_config = "mcp_servers.json"
    servers = json.load(open(servers_config))
    client = MultiServerMCPClient(
        servers['mcpServers'],
    )
    tools = await client.get_tools()
    agent = create_react_agent(model, tools)
    query = load_csv_prompt("outputs/JobPosts.csv")
    response = await agent.ainvoke(query)
    print(response)
    
if __name__ == "__main__":
    asyncio.run(main())
    