import pandas as pd
import json, re
import argparse

parser = argparse.ArgumentParser(description="Extract job postings from JSON output")
parser.add_argument("--json", default="outputs/sample_outputs.out", help="JSON path")
parser.add_argument("--output", default="outputs/JobPosts.csv", help="Output CSV path")
args = parser.parse_args()


rows = []
for line in open(args.jsonpath).readlines():
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