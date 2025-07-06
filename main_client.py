from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

import asyncio
import json
import os
import pandas as pd

from utils.prompt_working import llm_screening_prompt

# class ScreeningResponse(BaseModel):
#     title_pass: bool
#     experience_pass: bool
#     keep: bool
#     score: float
#     reason: str

async def main(idx=0, resume_path="data/full_resume.pdf"):
    model = ChatOllama(model="qwen3:8b")
    servers_config = "mcp_servers.json"
    servers = json.load(open(servers_config))
    client = MultiServerMCPClient(
        servers['mcpServers'],
    )
    tools = await client.get_tools()
    tool_names = [tool.name for tool in tools]
    # print(f"Loaded tools: {tool_names}")
    agent = create_react_agent(model, tools) # , response_format=("Please produce exactly this JSON", ScreeningResponse))
    job_df = pd.read_csv("outputs/JobPosts.csv")
    row = job_df.iloc[idx]
    position = "Machine Learning Engineer"
    # abs_resume_path = os.path.abspath(resume_path)
    query = llm_screening_prompt(row, position, resume_path)
    response = await agent.ainvoke(query)
    return response['messages']
    
if __name__ == "__main__":
    response = asyncio.run(main(0, "data/full_resume.pdf"))
    print(response[-1].content)