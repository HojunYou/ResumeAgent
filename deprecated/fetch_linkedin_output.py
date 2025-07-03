"""
fetch_linkedin_desc.py
----------------------
Read an output file (e.g. utils/sample_outputs.out), pull every LinkedIn job URL,
open the page, click “About the job → See more”, and save the full description
HTML for each job into a JSON file.

Usage
-----
uv pip install selenium bs4 rich
export LI_AT_COOKIE="..."  # optional LinkedIn session cookie
python utils/fetch_linkedin_desc.py \
       --input utils/sample_outputs.out \
       --output data/job_descriptions.json \
       --headless

Deprecated since scrap_linkedin.py stores descriptions in JSON.
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, pathlib
from typing import List, Dict
from bs4 import BeautifulSoup               # noqa
from rich.progress import track
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def iter_urls(path: str) -> List[str]:
    """Yield LinkedIn /jobs/view URLs found in a text‐like file."""
    for line in pathlib.Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        # last whitespace token
        candidate = line.split()[-1]
        if "linkedin.com/jobs" in candidate:
            yield candidate
        else:
            m = re.search(r"https://www\.linkedin\.com/jobs/view/[^\s]+", line)
            if m:
                yield m.group(0)


def init_driver(headless: bool = False) -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--window-size=1280,1024")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    if headless:
        opts.add_argument("--headless=new")
    driver = webdriver.Chrome(options=opts)

    # optional session cookie
    cookie_raw = os.getenv("LI_AT_COOKIE")
    if cookie_raw:
        # strip possible prefixes like "export LI_AT_COOKIE=" and quotes
        if "LI_AT_COOKIE" in cookie_raw:
            cookie_raw = cookie_raw.split("=", 1)[-1]
        cookie_raw = cookie_raw.strip().strip('\'"')
        driver.get("https://www.linkedin.com")  # must be on domain to set cookie
        driver.delete_all_cookies()
        driver.add_cookie({
            "name":   "li_at",
            "value":  cookie_raw,
            "domain": ".linkedin.com",
            "path":   "/",
            "secure": True,
            "httpOnly": True,
        })
        print("[info] li_at cookie injected OK")
    return driver


def scrape_job(url: str, driver: webdriver.Chrome, timeout: int = 15) -> str | None:
    """Return full HTML under the About-the-Job section."""
    driver.get(url)
    wait = WebDriverWait(driver, timeout)

    # --- expand “See more” if present ---------------------------------------
    see_more_selectors = [
        (By.CSS_SELECTOR, "button[aria-label^='See more']"),
        (By.CSS_SELECTOR, "button[aria-label*='See more about']"),
        (By.XPATH, "//button[.//span[contains(text(),'See more')]]"),
        (By.XPATH, "//button[contains(.,'See more')]"),
        (By.CSS_SELECTOR, "button[data-tracking-control-name*='description']"),
    ]
    for by, sel in see_more_selectors:
        try:
            btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((by, sel))
            )
            btn.click()
            break
        except TimeoutException:
            continue  # try the next selector

    try:
        # Locate <h2>About the job … then following div
        header = driver.find_element(
            By.XPATH,
            "//h2[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'about the job')]"
        )
        container = header.find_element(By.XPATH, "following-sibling::div")
        return container.get_attribute("innerHTML")
    except Exception as exc:
        print(f"[warn] {url[:80]} ... {exc}", file=sys.stderr)
        return None


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(
        description="Scrape full LinkedIn job descriptions into HTML."
    )
    ap.add_argument("--input", required=True, help="Text/CSV file with job URLs")
    ap.add_argument("--output", required=True, help="Output JSON path")
    ap.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True, help="Run Chrome headless")
    args = ap.parse_args()

    urls = list(iter_urls(args.input))
    if not urls:
        sys.exit("No LinkedIn job URLs found in input.")

    driver = init_driver(headless=args.headless)
    out: Dict[str, str] = {}
    try:
        for url in track(urls, description="Scraping LinkedIn"):
            html = scrape_job(url, driver)
            if html:
                out[url] = html
            time.sleep(4)  # polite delay
    finally:
        driver.quit()

    pathlib.Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"✅ {len(out)} descriptions saved → {args.output}")


if __name__ == "__main__":
    main()