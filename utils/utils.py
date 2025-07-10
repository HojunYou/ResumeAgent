import os
import pandas as pd
import json

def create_jobID(row: dict, position: str, unique_digits: int):
    # JobID: {company_name}_{positionabbr}_{unique 4 digits} # should be unique
    company_name = row['company'].lower().replace(' ', '_')
    position_abbr = ''.join(map(lambda x: x[0], position.lower().split(' ')))
    unique_digits_str = f"{unique_digits:04d}"
    return f"{company_name}_{position_abbr}_{unique_digits_str}"

def get_score_df(job_df: pd.DataFrame, save_path: str):
    if os.path.exists(save_path):
        score_df = pd.read_csv(save_path)
    else:
        # inherit all columns from job_df, but add JobID and scores from response
        score_df = job_df.copy()
        score_df['jobid'] = None
        score_df['score'] = None
        ## Make JobID comes first and score comes fifth
        score_df = score_df[['jobid', 'score'] + [col for col in score_df.columns if col not in ['jobid', 'score']]]
    return score_df

def parse_score_response(response: str) -> dict:
    ## remove content from <think> to </think>
    response_text = response.split('<think>')[1].split('</think>')[1]
    response_text = response_text.strip()
    try:
        result = json.loads(response_text)
    except Exception as e:
        print(f"Error parsing score response: {e}")
        print(f"Response: {response_text}")
        print(f"Returning empty dict")
        result = {
            "score": 0, 
            "reason": "Error parsing score response",
            "title_pass": False,
            "experience_pass": False,
            "skill_pass": False,
            "keep": False
        }
    return result

def update_score_df(score_df: pd.DataFrame, job_id: str, idx: int, response: dict, save_path: str):
    
    score_df.loc[idx, 'jobid'] = job_id
    if len(response['messages']) > 3:
        results = parse_score_response(response['messages'][4].content)
        score_df.loc[idx, 'score'] = results['score']
    else:
        score_df.loc[idx, 'score'] = 0
    score_df.to_csv(save_path, index=False)

    return score_df