import pandas as pd
import json, re
import argparse

def main():
    parser = argparse.ArgumentParser(description="Extract job postings from JSON output")
    parser.add_argument("--input", default="outputs/linkedin_outputs.out", help="JSON path")
    parser.add_argument("--output", default="outputs/JobPosts.csv", help="Output CSV path")
    args = parser.parse_args()

    rows = []
    for line in open(args.input).readlines():
        line = line.strip()
        if not line:
            continue
        # handle possible “[ON_DATA] {...}”
        if line.startswith("{"):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                try:
                    line = line.split('}')[0] + '}'
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"❌ Error parsing JSON: {line}")
                    continue
        else:
            m = re.search(r"\{.*\}$", line)
            if m:
                rows.append(json.loads(m.group(0)))

    df = pd.DataFrame(rows)
    df.to_csv(args.output, index=False)
    print(f"✅ saved → {args.output}")
    print(f"✅ {len(rows)} rows")
    print(df.head())

if __name__ == "__main__":
    main()
    