from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

import asyncio
import json
import os
import pandas as pd

from utils.prompt import (
    llm_screening_prompt, 
    resume_tailoring_prompt
 ) 
from utils.utils import create_jobID, get_score_df, update_score_df, convert_tex_to_pdf, filter_score_df

# Load API key from file
# with open(os.path.expanduser("~/.openai_key"), "r") as f:
#     openai_api_key = f.read().strip()

# openai_api_key = openai_api_key.split("\"")[1].strip()
# os.environ["OPENAI_API_KEY"] = openai_api_key

async def main(idx=0, resume_path="data/full_resume.pdf", save_path="outputs/JobScores.csv", threshold=0.6):
    model = ChatOllama(model="MFDoom/deepseek-r1-tool-calling:8b")
    # model = ChatOpenAI(model="o4-mini")
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
    # score_df = get_score_df(job_df, save_path)
    # job_id = create_jobID(row, position, idx)
    ## Step 1: Screening
    query = llm_screening_prompt(row, position, resume_path)
    screening_response = await agent.ainvoke(query)
    ## Step 2: Update score_df
    # print(f"Response: {screening_response}")
    # score_df = update_score_df(score_df, job_id, idx, screening_response, save_path)
    return screening_response['messages']
    # ## Step 3: Check if the job passed screening
    # updated_row = score_df.iloc[idx]
    # if updated_row['score'] > threshold:
    #     print(f"Job {job_id} passed screening with score {updated_row['score']}")
    # else:
    #     print(f"Job {job_id} failed screening with score {updated_row['score']}")
    # ## Step 4: Tailor .tex file
    # original_tex_path = resume_path.replace(".pdf", ".tex")
    # # resume_tex = open(original_tex_path, "r").read()
    # if updated_row['score'] >= threshold:
    #     query = updated_resume_tailoring_prompt(updated_row, original_tex_path)
    #     tailoring_response = await agent.ainvoke(query)
    #     try:
    #         results = json.loads(tailoring_response['messages'][-1].content)
    #         if results['success']:
    #             try:
    #                 convert_tex_to_pdf(results['saved_path'], os.path.dirname(results['saved_path']))
    #                 score_df = update_score_df(score_df, updated_row['jobid'], idx, tailoring_response, save_path, target_col='final_score')
    #                 print(f"Job {updated_row['jobid']} tailoring successful with final score {score_df.loc[idx, 'final_score']}")
    #             except Exception as e:
    #                 print(f"Error converting tex to pdf: {e}")
    #         else:
    #             print(f"Error tailoring resume: {results['error']}")
    #     except Exception as e:
    #         print(f"Error tailoring resume: {e}")
        
    #     filter_score_df(score_df, threshold, 'outputs/TargetJobs.csv')
    #     return tailoring_response['messages']
    # else:
    #     print(f"Job {updated_row['jobid']} failed screening with score {updated_row['score']}")
    #     return None
    
if __name__ == "__main__":
    response = asyncio.run(main(16, "data/full_resume.pdf"))
    if response:
        print(response[-1].content)
    else:
        print("No response")