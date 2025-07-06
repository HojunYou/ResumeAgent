from langchain_mcp_adapters.client import MultiServerMCPClient, load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
import asyncio
import json
import pandas as pd
from utils.prompt import initial_screening_prompt, llm_screening_prompt

async def main(idx=0, resume_path="data/full_resume.pdf"):
    model = ChatOllama(model="qwen3:8b")
    servers_config = "mcp_servers.json"
    servers = json.load(open(servers_config))
    client = MultiServerMCPClient(
        servers['mcpServers'],
    )
    tools = await client.get_tools()
    agent = create_react_agent(model, tools)
    job_df = pd.read_csv("outputs/JobPosts.csv")
    row = job_df.iloc[idx]
    position = "Machine Learning Engineer"
    query = llm_screening_prompt(row, position, resume_path)
    # query = load_csv_prompt("outputs/JobPosts.csv")
    response = await agent.ainvoke(query)
    return query['messages'], response
    # print(response)
    
if __name__ == "__main__":
    query, response = asyncio.run(main(2, "data/full_resume.pdf"))
    