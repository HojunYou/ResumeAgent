"""
JobSearchAgent
==============

• Discovers each company’s “careers” URL (cached in `data/company_cache.json`).
• Pulls postings via static HTML scraping or Greenhouse/Lever JSON when available.
• Filters postings by date, degree, and YOE.
• Returns a list of job dicts, capped at 6 per company, sorted by similarity-ready text.
"""
import os, re, datetime as dt, logging, json
import pandas as pd
from typing import List, Dict
import requests
from bs4 import BeautifulSoup

CACHE_PATH = os.path.join("data", "company_cache.json")
HEADERS    = {"User-Agent": "Mozilla/5.0 (ResumeAgent)"}

# --- helpers ---------------------------------------------------------------

def _parse_post_date(raw: str) -> dt.datetime | None:
    """Try a few date layouts → datetime, else None"""
    for fmt in ("%Y-%m-%d", "%b %d %Y", "%d %B %Y"):
        try:
            return dt.datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    return None

def _is_valid_url(url: str, timeout: int = 6) -> bool:
    """Quick HEAD check to confirm the careers URL is reachable (status < 400)."""
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout)
        return r.status_code < 400
    except requests.RequestException:
        return False

def _fill_placeholders(url: str, position: str, location: str | None) -> str:
    """Replace {position} and {location} placeholders with URL‑encoded values."""
    if "{position}" in url:
        url = url.replace("{position}", requests.utils.quote(position))
    if "{location}" in url and location:
        url = url.replace("{location}", requests.utils.quote(location))
    return url

# --- main class ------------------------------------------------------------

class JobSearchAgent:
    def __init__(
        self,
        companies_path: str | os.PathLike,
        position: str = "Machine Learning Engineer",
        location: str | None = "San Francisco",
        max_results: int = 50,
    ) -> None:
        self.position   = position
        self.location   = location
        self.max_total  = max_results
        self.company_df  = pd.read_csv(companies_path)
        # Make sure expected columns exist
        if "CareerURL" not in self.company_df.columns:
            self.company_df = self.company_df.assign(CareerURL=None)
        # convenience list of company names
        self.companies = self.company_df["Company"].to_list()
        self.companies_path = str(companies_path)
        self.logger     = logging.getLogger(self.__class__.__name__)
        self.cache      = self._load_cache()
        # sequential counter for human‑readable JobID generation
        self._id_counter = 0

    # ----------------- public API -----------------

    def search_jobs(self) -> List[Dict]:
        """
        High-level entry: returns list[{job_id, title, company, url, description, posted, yoe, edu, embed_score, llm_score}]
        Deduplicates by job_id, computes similarity scores, filters/ranks jobs, and outputs results to results/ directory as CSV.
        """
        # Step 0: make sure CareerURL column is populated/validated
        self.update_career_urls()
        all_results: list[dict] = []
        job_ids = set()
        for company in self.companies:
            try:
                results = self._search_company(company)
                # Deduplicate by job_id
                unique_jobs = []
                for job in results:
                    job_id = self._hash_job(job)
                    if job_id not in job_ids:
                        job["job_id"] = self._generate_job_id(job["company"])
                        job_ids.add(job_id)
                        unique_jobs.append(job)

                # Filter jobs and limit to 6 per company
                filtered = self._filter_jobs(unique_jobs)
                filtered = filtered[:6]
                all_results.extend(filtered)

            except Exception as exc:
                self.logger.warning("❌ %s – %s", company, exc)
            if len(all_results) >= self.max_total:
                break

        # sort by recency as tie-breaker
        all_results = sorted(all_results, key=lambda x: x["posted"], reverse=True)[: self.max_total]

        # Output DataFrame/CSV
        df = pd.DataFrame([
            {
                "JobID": job["job_id"],
                "CompanyName": job["company"],
                "JobTitle": job["title"],
                "JobDescriptionURL": job["url"],
                "PostedDate": job["posted"].strftime("%Y-%m-%d") if job.get("posted") else None,
            }
            for job in all_results
        ])
        os.makedirs("data", exist_ok=True)
        out_path = os.path.join("data", "job_results.csv")
        df.to_csv(out_path, index=False)
        self.logger.info(f"✅ Job discovery results saved to {out_path}")
        return all_results

    # ----------------- JobID helper -----------------
    _ALNUM_RE = re.compile(r"[a-z0-9]")

    def _generate_job_id(self, company: str) -> str:
        """JobID = POS<3> + CMP<3> + 4‑digit counter

        * POS<3> – first 3 alphanum chars from position
        * CMP<3> – abbreviation rule:
              • keep first alphanum char
              • drop vowels (a,e,i,o,u) in the rest
              • take the next 2 consonants/digits
              • pad with 'x' if needed
        The 4‑digit counter guarantees uniqueness even if two companies
        collide on the same abbreviation.
        """
        vowels = set("aeiou")
        def abbr(text: str) -> str:
            cleaned = "".join(self._ALNUM_RE.findall(text.lower()))
            if not cleaned:
                return "xxx"
            first = cleaned[0]
            rest = [ch for ch in cleaned[1:] if ch not in vowels]
            return (first + "".join(rest))[:3].ljust(3, "x")

        self._id_counter += 1
        return f"{abbr(self.position)}{abbr(company)}{self._id_counter:04d}"

    # ----------------- core steps -----------------

    def _search_company(self, company: str) -> list[dict]:
        """
        Discover and parse jobs for a single company. Modular for new job boards.
        """
        # 1.  Prefer the CareerURL already stored in company_df
        row_idx = self.company_df["Company"].to_list().index(company)
        stored_url = self.company_df.iloc[row_idx]["CareerURL"]

        careers_url = None
        if stored_url and _is_valid_url(stored_url):
            careers_url = stored_url
        else:
            # 2. Otherwise discover and (optionally) cache it
            careers_url = self._discover_careers_url(company)
            if not careers_url:
                raise RuntimeError("careers URL not found")
            # persist to dataframe and CSV for next run
            if _is_valid_url(careers_url):
                self.company_df.at[row_idx, "CareerURL"] = careers_url
                self.company_df.to_csv(self.companies_path, index=False)

        # Fill {position}/{location} placeholders
        # careers_url = _fill_placeholders(careers_url, self.position, self.location)

        # Store for output
        self.logger.info("✔ %s careers page: %s", company, careers_url)

        # Modular job board dispatch
        if any(board in careers_url for board in ("greenhouse.io", "boards.greenhouse.io")):
            jobs = self._parse_greenhouse(careers_url)
        elif any(board in careers_url for board in ("lever.co", "jobs.lever.co")):
            jobs = self._parse_lever(careers_url)
        elif any(board in careers_url for board in ("workdayjobs.com", "workday.com")):
            jobs = self._parse_workday(careers_url)
        else:
            jobs = self._parse_static_site(careers_url, company)
        # Attach company/careers_url for output
        for job in jobs:
            job["company"] = company
            job["careers_url"] = careers_url
        return jobs

    # ----------------- discover careers URL -----------------

    def _discover_careers_url(self, company: str) -> str | None:
        """
        Heuristic + search‑engine discovery of a company's public job board.

        Strategy
        --------
        1.  Try common patterns quickly ("/careers", Greenhouse, Lever, Workday).
        2.  Fallback to DuckDuckGo HTML search and extract the first
            result whose URL contains a careers keyword.
        3.  Cache the first working URL for next runs.
        """
        # 0.  Return cached hit
        if company in self.cache:
            return self.cache[company]

        slug = re.sub(r"[^a-z0-9]", "", company.lower())        # e.g. "Google" → "google"

        # 1. Pattern heuristics (fast, no search‐engine latency)
        patterns = [
            f"https://www.{slug}.com/careers",
            f"https://{slug}.com/careers",
            f"https://boards.greenhouse.io/{slug}",
            f"https://jobs.lever.co/{slug}",
            f"https://{slug}.workdayjobs.com/en-US/{slug}",
        ]
        for url in patterns:
            if _is_valid_url(url):
                self.cache[company] = url
                self._save_cache()
                return url

        # 2. DuckDuckGo fallback
        query = f"{company} careers jobs"
        try:
            resp  = requests.get(
                "https://duckduckgo.com/html/",
                params={"q": query},
                headers=HEADERS,
                timeout=10,
            )
            soup  = BeautifulSoup(resp.text, "html.parser")
            for a in soup.select("a.result__a[href]"):
                href = a["href"]
                # DuckDuckGo obfuscates links: /l/?kh=-1&uddg=<URL>
                if "uddg=" in href:
                    from urllib.parse import parse_qs, urlparse, unquote
                    qs = parse_qs(urlparse(href).query)
                    if "uddg" in qs:
                        href = unquote(qs["uddg"][0])
                if not href.startswith("http"):
                    continue
                if not any(k in href.lower() for k in ("careers", "jobs", "greenhouse", "lever.co", "workday")):
                    continue
                if _is_valid_url(href):
                    self.cache[company] = href
                    self._save_cache()
                    return href
        except requests.RequestException:
            pass  # swallow network issues; will return None

        # 3. Give up
        return None

    # ----------------- public util -----------------
    def update_career_urls(self) -> None:
        """
        Populate missing CareerURL column in data/company_list.csv.
        """
        self.logger.info(f"Updating career URLs for {self.position} and {self.location} for {len(self.company_df)} companies")
        updated_rows = []
        for _, row in self.company_df.iterrows():
            filled = _fill_placeholders(row["CareerURL"], self.position, self.location)
            if filled and _is_valid_url(filled):
                row["CareerURL"] = filled
                updated_rows.append(row)
                continue

            url = self._discover_careers_url(row["Company"])
            if url and _is_valid_url(url):
                row["CareerURL"] = _fill_placeholders(url, self.position, self.location)
            updated_rows.append(row)

        # Save back if anything changed
        new_df = pd.DataFrame(updated_rows)
        if not new_df.equals(self.company_df):
            safe_position = re.sub(r'\W+', '_', self.position).lower()
            new_path = self.companies_path.replace(
                ".csv", f"_{safe_position}.csv"
            )
            new_df.to_csv(new_path, index=False)
            self.logger.info(f"✅ Career URLs updated in {new_path}")
        self.company_df = new_df

    # ----------------- site-specific parsers -----------------

    def _parse_greenhouse(self, url: str) -> list[dict]:
        resp = requests.get(url + ".json", headers=HEADERS, timeout=7).json()
        jobs = []
        for post in resp.get("jobs", []):
            jobs.append(
                dict(
                    id       = post["id"],
                    title    = post["title"],
                    url      = post["absolute_url"],
                    description = BeautifulSoup(post["content"], "html.parser").get_text(" ", strip=True),
                    posted   = _parse_post_date(post["updated_at"][:10]) or dt.datetime.utcnow(),
                    company  = resp["company"]["name"],
                    location = post["location"]["name"],
                )
            )
        return jobs

    def _parse_lever(self, url: str) -> list[dict]:
        api = url.rstrip("/") + ".json"
        posts = requests.get(api, headers=HEADERS, timeout=7).json()
        jobs = []
        for post in posts:
            jobs.append(
                dict(
                    id          = post["id"],
                    title       = post["text"],
                    url         = post["hostedUrl"],
                    description = BeautifulSoup(post["description"], "html.parser").get_text(" ", strip=True),
                    posted      = _parse_post_date(post["createdAt"][:10]) or dt.datetime.utcnow(),
                    company     = post["categories"].get("team", ""),
                    location    = post["categories"].get("location", ""),
                )
            )
        return jobs

    def _parse_static_site(self, url: str, company: str) -> list[dict]:
        """
        Very lightweight scraper for companies that don't expose JSON APIs.
        Strategy:
        1. Look for <a> tags whose text matches the position string.
        2. If none found (common on React sites e.g. Apple), parse any embedded
           <script type="application/ld+json"> that contains an ItemList / jobs.
        """
        resp  = requests.get(url, headers=HEADERS, timeout=10)
        soup  = BeautifulSoup(resp.text, "html.parser")
        jobs  = []

        # -- 1. Anchor‑based fallback ------------------------------------------------
        for a in soup.find_all("a", href=True, text=re.compile(self.position, re.I)):
            print(a)
            jobs.append(
                dict(
                    id          = self._generate_job_id(company),
                    title       = a.get_text(strip=True),
                    url         = requests.compat.urljoin(url, a["href"]),
                    description = f"{a.get_text(strip=True)} at {company}",
                    posted      = dt.datetime.utcnow(),
                    company     = company,
                    location    = self.location or "",
                )
            )
        if jobs:
            return jobs

        # -- 2. ld+json / React initial‑state parsing --------------------------------
        for script in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(script.string)
            except (ValueError, TypeError):
                continue
            # Apple Search returns an ItemList
            if isinstance(data, dict) and data.get("@type") == "ItemList":
                for idx, item in enumerate(data.get("itemListElement", []), 1):
                    ent = item.get("item", {})
                    title = ent.get("title") or ent.get("name") or ""
                    if self.position.lower() not in title.lower():
                        continue
                    jobs.append(
                        dict(
                            id          = self._generate_job_id(company),
                            title       = title,
                            url         = ent.get("url") or url,
                            description = ent.get("description", title),
                            posted      = dt.datetime.utcnow(),
                            company     = company,
                            location    = ent.get("jobLocation", [{}])[0]
                                            .get("address", {})
                                            .get("addressLocality", self.location or ""),
                        )
                    )
            # break early if we already captured some jobs
            if jobs:
                break

        return jobs

    # ----------------- filtering -----------------

    _YOE_RE  = re.compile(r"(\d+)\+?\s+(?:years|yrs)", re.I)
    _DEGREE  = re.compile(r"(ph\.?d|master'?s|mphil|md)", re.I)

    def _filter_jobs(self, jobs: list[dict]) -> list[dict]:
        keep: list[dict] = []
        for j in jobs:
            # Years of experience filter (<= 2-8 is typical MLE bar – adjust as needed)
            years_req = self._extract_yoe(j["description"])
            if years_req and years_req > 8:
                continue

            # Degree filter – you have a PhD, so no restriction
            # Posting recency – last 60 days
            if (dt.datetime.utcnow() - j["posted"]).days > 60:
                continue

            # Title must roughly match asked position
            if self.position.lower() not in j["title"].lower():
                continue

            keep.append(j)

        # Sort newest first
        return sorted(keep, key=lambda x: x["posted"], reverse=True)

    @staticmethod
    def _extract_yoe(text: str | None) -> int | None:
        if not text:
            return None
        m = JobSearchAgent._YOE_RE.search(text)
        return int(m.group(1)) if m else None

    # ----------------- cache helpers -----------------

    def _load_cache(self) -> dict:
        if os.path.exists(CACHE_PATH):
            return json.loads(open(CACHE_PATH).read())
        return {}

    def _save_cache(self) -> None:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w") as fp:
            json.dump(self.cache, fp, indent=2)
