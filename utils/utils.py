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

def parse_score_response(response: str):
    ## remove content from <think> to </think>
    response = response.split('<think>')[1].split('</think>')[1]
    response = response.strip()
    try:
        response = json.loads(response)
    except Exception as e:
        print(f"Error parsing score response: {e}")
        print(f"Response: {response}")
        print(f"Returning empty dict")
        response = {}
    return response