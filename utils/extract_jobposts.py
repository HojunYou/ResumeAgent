import pandas as pd
import json, re
import argparse
from scrap_linkedin import ABBREVIATIONS

def main():
    parser = argparse.ArgumentParser(description="Extract job postings from JSON output")
    parser.add_argument('--position', default="Machine Learning Engineer", help="Job position keyword, e.g. 'Machine Learning Engineer'")
    parser.add_argument("--input", default="outputs/sample_outputs.out", help="JSON path")
    parser.add_argument("--output", default="outputs/JobPosts.csv", help="Output CSV path")
    args = parser.parse_args()

    abbr = ABBREVIATIONS.get(args.position.lower(), args.position)
    args.input = args.input[:-4] + f"_{abbr}.out"
    args.output = args.output[:-4] + f"_{abbr}.csv"

    rows = []
    for line in open(args.input).readlines():
        line = line.strip()
        if not line:
            continue
        # handle possible “[ON_DATA] {...}”
        if line.startswith("{"):
            rows.append(json.loads(line))
        else:
            m = re.search(r"\{.*\}$", line)
            if m:
                rows.append(json.loads(m.group(0)))

    df = pd.DataFrame(rows)
    df.to_csv(args.output, index=False)
    print(f"✅ saved → {args.output}")
    print(df.head())

if __name__ == "__main__":
    main()
    