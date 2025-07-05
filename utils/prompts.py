
def load_csv_prompt(csv_path):
    prompt = f"""
    Load job postings from CSV file:
    {csv_path}

    Return a list of job dicts. No other text.
    """
    return {"messages": prompt}

def fetch_tex_prompt(path):
    prompt = f"""
    Read LaTeX resume file content as text.
    {path}
    Return the text content. No other text."""
    return {"messages": prompt}

def fetch_pdf_prompt(path):
    prompt = f"""
    Read PDF resume file content as text.
    {path}
    Return the text content. No other text."""
    return {"messages": prompt}

    
    