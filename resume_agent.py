import json
import os
import logging
import pandas as pd
from typing import Any, Dict
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from utils.prompt import llm_screening_prompt, resume_tailoring_prompt
from utils.utils import create_jobID, update_score_df, convert_tex_to_pdf

class ResumeAgent:
    def __init__(self, model: ChatOpenAI, tools: list, position: str, resume_path: str, threshold: float = 0.6):
        self.model = model
        self.tools = tools
        self.agent = create_react_agent(model, tools)
        self.position = position
        self.resume_path = resume_path
        self.threshold = threshold
        
    async def process_job_posting(self, row: pd.Series, idx: Any, score_df: pd.DataFrame, save_path: str) -> Dict[str, Any]:
        """Process a single job posting through screening and tailoring."""
        job_id = create_jobID(row, self.position, idx)
        logging.info(f"Processing job {idx + 1}: {row['title']} at {row['company']}")
        
        # Step 1: Initial screening
        screening_query = llm_screening_prompt(row, self.position, self.resume_path)
        screening_response = await self.agent.ainvoke(screening_query)
        
        # Update score_df with screening results
        score_df = update_score_df(score_df, job_id, idx, screening_response, save_path)
        
        # Check if job passed initial screening
        if score_df.loc[idx, 'score'] > self.threshold:  # threshold
            logging.info(f"Job {job_id} passed screening with score {score_df.loc[idx, 'score']}")
            
            # Step 2: Resume tailoring
            tailoring_query = resume_tailoring_prompt(row, self.resume_path.replace('.pdf', '.tex'))
            tailoring_response = await self.agent.ainvoke(tailoring_query)
            
            # Parse tailoring response
            try:
                results = json.loads(tailoring_response['messages'][-1].content)
                if results.get('success', False):
                    # Convert tailored resume to PDF
                    tex_path = results.get('saved_path', '')
                    if tex_path and os.path.exists(tex_path):
                        pdf_result = convert_tex_to_pdf(tex_path, os.path.dirname(tex_path))
                        if pdf_result == "success":
                            # Update final score
                            score_df = update_score_df(score_df, job_id, idx, tailoring_response, save_path, target_col='final_score')
                            logging.info(f"Job {job_id} tailoring successful with final score {score_df.loc[idx, 'final_score']}")
                            return {
                                'success': True,
                                'job_id': job_id,
                                'screening_score': score_df.loc[idx, 'score'],
                                'final_score': score_df.loc[idx, 'final_score'],
                                'tex_path': tex_path
                            }
                        else:
                            logging.error(f"PDF conversion failed for {job_id}: {pdf_result}")
                    else:
                        logging.error(f"Tailored resume file not found for {job_id}")
                else:
                    logging.error(f"Tailoring failed for {job_id}: {results.get('error', 'Unknown error')}")
            except Exception as e:
                logging.error(f"Error parsing tailoring response for {job_id}: {e}")
        else:
            logging.info(f"Job {job_id} failed screening with score {score_df.loc[idx, 'score']}")
        
        return {'success': False, 'job_id': job_id}

async def setup_model_and_tools() -> tuple[ChatOpenAI, list]:
    """Setup the model and MCP tools."""
    # Load API key from file
    with open(os.path.expanduser("~/.openai_key"), "r") as f:
        openai_api_key = f.read().strip()
    
    openai_api_key = openai_api_key.split("\"")[1].strip()
    os.environ["OPENAI_API_KEY"] = openai_api_key
    
    # Initialize model
    model = ChatOpenAI(model="o4-mini")
    
    # Load MCP servers and create client
    servers_config = "mcp_servers.json"
    servers = json.load(open(servers_config))
    client = MultiServerMCPClient(servers['mcpServers'])
    tools = await client.get_tools()
    
    return model, tools