import pandas as pd
import json
import re
from pathlib import Path

# --- File paths ---
BASE_DIR = Path(__file__).parent.parent
company_csv = BASE_DIR / "data/company_list.csv"
sample_outputs = BASE_DIR / "utils/sample_outputs.txt"
desc_json = BASE_DIR / "utils/sample_desc.json"
output_path = BASE_DIR / "outputs/enriched_company_list.csv"

# --- Step 1: Parse [ON_DATA] lines from sample_outputs.txt ---
on_data_pattern = re.compile(r"^\[ON_DATA\] (.*?), (.*?), (.*?) (.*?) (https://www.linkedin.com/jobs/view/[^ ]+) ?\[.*\] ?(\d+)")
# Fallback: Split by whitespace and try to extract URL

def parse_on_data_lines(filepath):
    results = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("[ON_DATA]"):
                # Try to extract using regex
                m = re.search(r"^\\[ON_DATA\\](.*?) (https://www.linkedin.com/jobs/view/[^ ]+)[^\[]*\\[.*$", line)
                if m:
                    prefix = m.group(1).strip()
                    url = m.group(2).strip()
                    # Try to extract company name from prefix (last word before URL)
                    parts = prefix.split()
                    if len(parts) >= 2:
                        company = parts[-2]
                        title = " ".join(parts[:-2])
                    else:
                        company = parts[-1] if parts else ""
                        title = ""
                    results.append({"company": company, "title": title, "url": url})
    return results

# --- Step 2: Build company → list of (job url, job title) ---
def build_company_job_map(on_data):
    mapping = {}
    for entry in on_data:
        company = entry["company"].strip()
        url = entry["url"].strip()
        title = entry["title"].strip()
        mapping.setdefault(company, []).append({"url": url, "title": title})
    return mapping

# --- Step 3: Load job descriptions ---
def load_desc_map(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Step 4: Merge with company_list.csv ---
def enrich_company_list():
    df = pd.read_csv(company_csv)
    on_data = parse_on_data_lines(sample_outputs)
    company_jobs = build_company_job_map(on_data)
    desc_map = load_desc_map(desc_json)

    # Add columns for job URLs and Descriptions
    job_urls_col = []
    job_descs_col = []
    for _, row in df.iterrows():
        cname = row["Company"].strip()
        jobs = company_jobs.get(cname, [])
        urls = [j["url"] for j in jobs]
        descs = [desc_map.get(url, "") for url in urls]
        job_urls_col.append(";".join(urls))
        job_descs_col.append("|||".join(descs))
    df["JobURLs"] = job_urls_col
    df["JobDescriptions"] = job_descs_col
    output_path.parent.mkdir(exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Enriched company list saved to {output_path}")

if __name__ == "__main__":
    enrich_company_list()
