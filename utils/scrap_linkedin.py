import logging
from linkedin_jobs_scraper import LinkedinScraper
from linkedin_jobs_scraper.events import Events, EventData, EventMetrics
from linkedin_jobs_scraper.query import Query, QueryOptions, QueryFilters
from linkedin_jobs_scraper.filters import (
    RelevanceFilters,
    # TimeFilters,
    TypeFilters,
    # ExperienceLevelFilters,
    # OnSiteOrRemoteFilters,
    # SalaryBaseFilters
)
import argparse, os
import pandas as pd
# ----------------- CLI -----------------
parser = argparse.ArgumentParser(description="Scrape LinkedIn jobs by company list")
parser.add_argument("--position", default="Machine Learning Engineer", help="Job position keyword, e.g. 'Machine Learning Engineer'")
parser.add_argument("--location", default="San Jose", help="Job location, e.g. 'San Francisco Bay Area'")
parser.add_argument("--filepath", default="data/company_small_list.csv", help="CSV with LinkedinURL column")
args = parser.parse_args()

position = args.position
location = args.location
csv_path = args.filepath

# Change root logger level (default is WARN)
logging.basicConfig(level=logging.INFO) # , format='%(asctime)s - %(levelname)s - %(message)s')

# Fired once for each successfully processed job
def on_data(data: EventData):
    print('[ON_DATA]', data.title, f"<<{data.company}>>", data.company_link, data.date, data.date_text, data.link, data.insights,
          len(data.description))

# Fired once for each page (25 jobs)
def on_metrics(metrics: EventMetrics):
    print('[ON_METRICS]', str(metrics))

def on_error(error):
    print('[ON_ERROR]', error)

def on_end():
    print('[ON_END]')

scraper = LinkedinScraper(
    chrome_executable_path=None,  # Custom Chrome executable path (e.g. /foo/bar/bin/chromedriver)
    chrome_binary_location=None,  # Custom path to Chrome/Chromium binary (e.g. /foo/bar/chrome-mac/Chromium.app/Contents/MacOS/Chromium)
    chrome_options=None,  # Custom Chrome options here
    headless=True,  # Overrides headless mode only if chrome_options is None
    max_workers=1,  # How many threads will be spawned to run queries concurrently (one Chrome driver for each thread)
    slow_mo=2,  # Slow down the scraper to avoid 'Too many requests 429' errors (in seconds)
    page_load_timeout=40  # Page load timeout (in seconds)    
)

# Add event listeners
scraper.on(Events.DATA, on_data)
scraper.on(Events.ERROR, on_error)
scraper.on(Events.END, on_end)

# ----------------- Build company‑specific queries -----------------
if not os.path.isfile(csv_path):
    raise FileNotFoundError(csv_path)

df = pd.read_csv(csv_path)

queries = []
for _, row in df.iterrows():
    url = row.get("LinkedinURL")
    if not url or not isinstance(url, str):
        logging.warning("No valid LinkedinURL found for company: %s", row.get("Company"))
        continue
    queries.append(
        Query(
            query=position,
            options=QueryOptions(
                locations=[location],
                apply_link=True,  # Try to extract apply link (easy applies are skipped). If set to True, scraping is slower because an additional page must be navigated. Default to False.
                skip_promoted_jobs=True,  # Skip promoted jobs. Default to False.
                page_offset=0,  # How many pages to skip
                limit=5,
                filters=QueryFilters(
                    company_jobs_url=url if url else None,
                    relevance=RelevanceFilters.RECENT,
                    # time=TimeFilters.MONTH,
                    type=[TypeFilters.FULL_TIME], #, TypeFilters.INTERNSHIP],
                    # on_site_or_remote=[OnSiteOrRemoteFilters.REMOTE],
                    # experience=[
                    #     ExperienceLevelFilters.ENTRY_LEVEL, 
                    #     ExperienceLevelFilters.ASSOCIATE,
                    #     ExperienceLevelFilters.MID_SENIOR
                    # ],
                    # base_salary=SalaryBaseFilters.SALARY_100K
                )
            )
        )
    )
if not queries:
    raise RuntimeError("No valid LinkedinURL found in the company list.")

companies = df["Company"].tolist()
scraper.run(queries, companies = companies)