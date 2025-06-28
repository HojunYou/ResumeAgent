"""
JobSearchAgent
==============

• Discovers each company’s “careers” URL (cached in `data/company_cache.json`).
• Pulls postings via static HTML scraping or Greenhouse/Lever JSON when available.
• Filters postings by date, degree, and YOE.
• Returns a list of job dicts, capped at 6 per company, sorted by similarity-ready text.
"""
from __future__ import annotations
import re, pathlib, datetime as dt, hashlib, logging
from typing import List, Dict
import requests
from bs4 import BeautifulSoup

CACHE_PATH = pathlib.Path("data/company_cache.json")
HEADERS    = {"User-Agent": "Mozilla/5.0 (ResumeAgent)"}

# --- helpers ---------------------------------------------------------------

def _slugify(text: str) -> str:
    return re.sub(r"[^\w\-]+", "_", text.lower()).strip("_")

def _hash(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:12]

def _parse_post_date(raw: str) -> dt.datetime | None:
    """Try a few date layouts → datetime, else None"""
    for fmt in ("%Y-%m-%d", "%b %d %Y", "%d %B %Y"):
        try:
            return dt.datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    return None

# --- main class ------------------------------------------------------------

class JobSearchAgent:
    def __init__(
        self,
        companies_path: pathlib.Path,
        position: str,
        location: str | None = "California Bay Area",
        max_results: int = 50,
    ) -> None:
        self.position   = position
        self.location   = location
        self.max_total  = max_results
        self.companies  = [c.strip() for c in open(companies_path).read().splitlines() if c.strip()]
        self.logger     = logging.getLogger(self.__class__.__name__)
        self.cache      = self._load_cache()

    # ----------------- public API -----------------

    def search_jobs(self, resume_path: pathlib.Path = None) -> List[Dict]:
        """
        High-level entry: returns list[{job_id, title, company, url, description, posted, yoe, edu, embed_score, llm_score}]
        Deduplicates by job_id, computes similarity scores, filters/ranks jobs, and outputs results to results/ directory as CSV.
        """
        import pandas as pd
        import utils.similarity as sim
        from collections import defaultdict

        if resume_path is None:
            raise ValueError("resume_path must be provided for similarity scoring.")
        resume_text = self._extract_resume_text(resume_path)

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
                        job["job_id"] = job_id
                        job_ids.add(job_id)
                        unique_jobs.append(job)
                # Compute similarity scores
                for job in unique_jobs:
                    try:
                        job["embed_score"] = sim.get_embed_score(resume_text, job.get("description", ""))
                    except Exception as e:
                        self.logger.warning(f"Embedding similarity failed for job {job['job_id']}: {e}")
                        job["embed_score"] = 0.0
                    try:
                        job["llm_score"] = sim.get_llm_score(resume_text, job.get("description", ""))
                    except Exception as e:
                        self.logger.warning(f"LLM similarity failed for job {job['job_id']}: {e}")
                        job["llm_score"] = 0.0
                # Filter and rank jobs
                filtered = self._filter_and_rank_jobs(unique_jobs)
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
                "EmbedScore": round(job.get("embed_score", 0), 3),
                "LLMScore": round(job.get("llm_score", 0), 3),
                "CompanyName": job["company"],
                "CareerWebsite": job["careers_url"],
                "JobDescriptionURL": job["url"],
            }
            for job in all_results
        ])
        results_dir = pathlib.Path("results")
        results_dir.mkdir(exist_ok=True)
        out_path = results_dir / "job_results.csv"
        df.to_csv(out_path, index=False)
        self.logger.info(f"✅ Results saved to {out_path}")
        return all_results

    def _extract_resume_text(self, resume_path: pathlib.Path) -> str:
        """Extracts text from a PDF resume using requests to local OCR or PDF-to-text endpoint, or fallback."""
        # For now, use agent_runner/tools.fetch_pdf_as_text logic or fallback to PyPDF2
        try:
            import PyPDF2
            with open(resume_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                return "\n".join(page.extract_text() or '' for page in reader.pages)
        except Exception as e:
            self.logger.warning(f"Failed to extract resume text: {e}")
            return ""

    def _hash_job(self, job: dict) -> str:
        """Generate a short, human-friendly job ID: {company}_{title}_{hash4}, all lowercase."""
        import re
        def prefix(text):
            return ''.join(re.findall(r'[a-z0-9]', text.lower()))[:3]
        company_prefix = prefix(job.get('company', ''))
        title_prefix = prefix(job.get('title', ''))
        base = f"{job.get('company','')}|{job.get('title','')}|{job.get('url','')}"
        short_hash = str(abs(hash(base)))[-4:]
        return f"{company_prefix}_{title_prefix}_{short_hash}"

    def _filter_and_rank_jobs(self, jobs: list[dict]) -> list[dict]:
        """
        Filter by years of experience, education, and date; rank by llm_score then embed_score, then recency.
        """
        filtered = [
            job for job in jobs
            if (job.get("yoe", 0) >= 2) and (job.get("edu", "").lower() in ["bachelor", "master", "phd"]) and job.get("posted")
        ]
        filtered = sorted(
            filtered,
            key=lambda x: (x.get("llm_score", 0), x.get("embed_score", 0), x["posted"]),
            reverse=True
        )
        return filtered

    # ----------------- core steps -----------------

    def _search_company(self, company: str) -> list[dict]:
        """
        Discover and parse jobs for a single company. Modular for new job boards.
        """
        careers_url = self._discover_careers_url(company)
        if not careers_url:
            raise RuntimeError("careers URL not found")

        # Store for output
        self.logger.info(f"Company: {company} | Careers URL: {careers_url}")

        # Modular job board dispatch
        if any(board in careers_url for board in ("greenhouse.io", "boards.greenhouse.io")):
            jobs = self._parse_greenhouse(careers_url)
        elif any(board in careers_url for board in ("lever.co", "jobs.lever.co")):
            jobs = self._parse_lever(careers_url)
        else:
            jobs = self._parse_static_html(careers_url)
        # Attach company/careers_url for output
        for job in jobs:
            job["company"] = company
            job["careers_url"] = careers_url
        return jobs

    # ----------------- discover careers URL -----------------

    def _discover_careers_url(self, company: str) -> str | None:
        if company in self.cache:
            return self.cache[company]

        query = f"{company} careers"
        resp  = requests.get("https://duckduckgo.com/html/", params={"q": query}, headers=HEADERS, timeout=7)
        soup  = BeautifulSoup(resp.text, "html.parser")
        for a in soup.select("a.result__a"):
            href = a["href"]
            if any(token in href for token in ("careers", "jobs", "jobs/results", "boards.greenhouse")):
                self.cache[company] = href
                self._save_cache()
                return href
        return None

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

    def _parse_static_site(self, url: str) -> list[dict]:
        resp  = requests.get(url, headers=HEADERS, timeout=10)
        soup  = BeautifulSoup(resp.text, "html.parser")
        jobs  = []
        for a in soup.find_all("a", href=True, text=re.compile(self.position, re.I)):
            jobs.append(
                dict(
                    id          = _hash(a["href"] + a.get_text()),
                    title       = a.get_text(strip=True),
                    url         = requests.compat.urljoin(url, a["href"]),
                    description = f"{a.get_text(strip=True)} at {url}",
                    posted      = dt.datetime.utcnow(),
                    company     = url.split("//")[1].split("/")[0],
                    location    = self.location or "",
                )
            )
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
        if CACHE_PATH.exists():
            return json.loads(CACHE_PATH.read_text())
        return {}

    def _save_cache(self) -> None:
        CACHE_PATH.write_text(json.dumps(self.cache, indent=2))