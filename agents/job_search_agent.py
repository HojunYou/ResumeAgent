"""
Agent for searching jobs from LinkedIn and company career pages.
"""
from typing import List, Dict

from bs4 import BeautifulSoup
import requests

class JobSearchAgent:
    def __init__(self, companies_path, position, location, max_results):
        self.companies_path = companies_path
        self.position = position
        self.location = location
        self.max_results = max_results

    def fetch_job_description_from_url(self, url):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Try to find main job description text
            for id_candidate in ['jobDescriptionText', 'job-description', 'description', 'job-desc', 'job-details']:
                desc = soup.find(id=id_candidate)
                if desc:
                    return desc.get_text(separator=' ', strip=True)
            # Fallback: find largest <div> or <section> with lots of text
            candidates = soup.find_all(['div', 'section'], recursive=True)
            best = max(candidates, key=lambda x: len(x.get_text()), default=None)
            if best:
                return best.get_text(separator=' ', strip=True)
            # Last fallback: whole page text
            return soup.get_text(separator=' ', strip=True)
        except Exception as e:
            return None

    def search_jobs(self) -> List[Dict]:
        """
        Returns a list of job dicts with keys: title, company, url, description.
        TODO: Implement LinkedIn and company site scraping. Here, just a mock example for demonstration.
        """
        # Example mock jobs for demonstration
        jobs = [
            {
                'title': self.position,
                'company': 'Google',
                'url': 'https://careers.google.com/jobs/results/',
            },
            {
                'title': self.position,
                'company': 'Microsoft',
                'url': 'https://careers.microsoft.com/us/en',
            },
            {
                'title': self.position,
                'company': 'Meta (Facebook)',
                'url': 'https://www.metacareers.com/jobs/',
            },
            {
                'title': self.position,
                'company': 'Apple',
                'url': 'https://jobs.apple.com/en-us/search',
            },
        ]
        for job in jobs:
            if job.get('url'):
                desc = self.fetch_job_description_from_url(job['url'])
                job['description'] = desc if desc else f"No description found for {job['company']}"
        return jobs[:self.max_results]
