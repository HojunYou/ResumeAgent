from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

import asyncio
import json
import os
import pandas as pd

from utils.prompt import initial_screening_prompt, llm_screening_prompt

# class ScreeningResponse(BaseModel):
#     title_pass: bool
#     experience_pass: bool
#     keep: bool
#     score: float
#     reason: str

async def main(indices=[0], resume_path="data/full_resume.pdf"):
    if isinstance(indices, int):
        indices = [indices]
    model = ChatOllama(model="qwen3:8b")
    servers_config = "mcp_servers.json"
    servers = json.load(open(servers_config))
    client = MultiServerMCPClient(
        servers['mcpServers'],
    )
    tools = await client.get_tools()
    tool_names = [tool.name for tool in tools]
    print(f"Loaded tools: {tool_names}")
    agent = create_react_agent(model, tools) # , response_format=("Please produce exactly this JSON", ScreeningResponse))
    job_df = pd.read_csv("outputs/JobPosts.csv")
    responses = []
    for idx in indices:
        row = job_df.iloc[idx]
        position = "Machine Learning Engineer"
        abs_resume_path = os.path.abspath(resume_path)
        query = llm_screening_prompt(row, position, abs_resume_path)
        # query = load_csv_prompt("outputs/JobPosts.csv")
        response = await agent.ainvoke(query)
        responses.append(response)
    return responses
    # print(response)
    
if __name__ == "__main__":
    responses = asyncio.run(main([2], "data/full_resume.pdf"))
    for response in responses:
        print(response)