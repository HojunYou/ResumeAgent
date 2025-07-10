from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

import asyncio
import json
import os
import pandas as pd

from utils.prompt_working import llm_screening_prompt, fetch_tex_prompt
from utils.utils import create_jobID, get_score_df, parse_score_response, update_score_df

# class ScreeningResponse(BaseModel):
#     title_pass: bool
#     experience_pass: bool
#     keep: bool
#     score: float
#     reason: str

async def main(idx=0, resume_path="data/full_resume.pdf", save_path="outputs/JobScores.csv", threshold=0.75):
    model = ChatOllama(model="qwen3:8b")
    servers_config = "mcp_servers.json"
    servers = json.load(open(servers_config))
    client = MultiServerMCPClient(
        servers['mcpServers'],
    )
    tools = await client.get_tools()
    # tool_names = [tool.name for tool in tools]
    # print(f"Loaded tools: {tool_names}")
    agent = create_react_agent(model, tools) # , response_format=("Please produce exactly this JSON", ScreeningResponse))
    job_df = pd.read_csv("outputs/JobPosts.csv")
    row = job_df.iloc[idx]
    position = "Machine Learning Engineer"
    score_df = get_score_df(job_df, save_path)
    job_id = create_jobID(row, position, idx)
    ## Step 1: Screening
    # query = llm_screening_prompt(row, position, resume_path)
    # response = await agent.ainvoke(query)
    ## Step 2: Update score_df
    # score_df = update_score_df(score_df, job_id, idx, response, save_path)
    ## Step 3: Check if the job passed screening
    updated_row = score_df.iloc[idx]
    if updated_row['score'] > threshold:
        print(f"Job {job_id} passed screening with score {updated_row['score']}")
    else:
        print(f"Job {job_id} failed screening with score {updated_row['score']}")
    ## Step 4: Tailor .tex file
    tex_response = await agent.ainvoke(fetch_tex_prompt(resume_path.replace(".pdf", ".tex")))
    return tex_response['messages']
    
if __name__ == "__main__":
    response = asyncio.run(main(9, "data/full_resume.pdf")) #"/Users/hojunyou/Dropbox/Projects/ResumeAgent/data/full_resume.pdf" 
    print(response[-1].content)