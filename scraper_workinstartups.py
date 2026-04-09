"""
WorkInStartups.com scraper — UK startup job board.
Good coverage of London startups, often has roles not on bigger boards.
"""

import time
import random
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}

_SEARCH_TERMS = [
    "chief of staff",
    "head of operations",
    "commercial lead",
    "business development",
    "coo",
    "general manager",
]


def _fetch(url: str, retries: int = 3) -> str | None:
    session = requests.Session()
    session.headers.update(_HEADERS)
    for i in range(retries):
        try:
            time.sleep(random.uniform(1.5, 3.5) + i * 2)
            r = session.get(url, timeout=15)
            if r.status_code == 200:
                return r.text
        except Exception as e:
            logger.debug(f"WorkInStartups fetch error: {e}")
    return None


def _parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    cards = soup.select(
        "div.job, article.job, div[class*='job-item'], "
        "li.job-listing, div[class*='vacancy']"
    )
    if not cards:
        cards = soup.select("div.card, article.listing, div.result")

    for card in cards:
        try:
            title_el   = card.select_one("h2, h3, h4, [class*='title'], [class*='job-title']")
            company_el = card.select_one("[class*='company'], [class*='employer']")
            loc_el     = card.select_one("[class*='location'], [class*='loc']")
            salary_el  = card.select_one("[class*='salary']")
            link_el    = card.select_one("a")

            if not title_el:
                continue

            href = ""
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("/"):
                    href = f"https://workinstartups.com{href}"

            jobs.append({
                "title":    title_el.get_text(strip=True),
                "company":  company_el.get_text(strip=True) if company_el else "Unknown",
                "location": loc_el.get_text(strip=True) if loc_el else "UK",
                "salary":   salary_el.get_text(strip=True) if salary_el else None,
                "url":      href or "https://workinstartups.com/job-board",
                "summary":  "",
                "tags":     ["WorkInStartups", "UK Startup"],
                "match_tags": [],
                "posted_date": None,
                "source":   "WorkInStartups",
                "sponsorship_likely": True,
                "score": 0, "score_reason": "",
            })
        except Exception as e:
            logger.debug(f"WorkInStartups parse error: {e}")

    return jobs


def scrape_workinstartups(max_results: int = 20) -> list[dict]:
    """Scrape WorkInStartups.com for relevant roles."""
    all_jobs = []

    for term in _SEARCH_TERMS[:4]:
        encoded = requests.utils.quote(term)
        url = f"https://workinstartups.com/job-board/search/{encoded}/"
        html = _fetch(url)
        if html:
            jobs = _parse(html)
            all_jobs.extend(jobs)

    if not all_jobs:
        return [{
            "title":    "WorkInStartups — job search",
            "company":  "Browse on WorkInStartups",
            "location": "UK",
            "salary":   None,
            "url":      "https://workinstartups.com/job-board/search/chief-of-staff/",
            "summary":  "WorkInStartups scraper returned no results. Click to browse directly.",
            "tags":     ["WorkInStartups", "UK Startup"],
            "match_tags": [],
            "posted_date": None,
            "source":   "WorkInStartups",
            "sponsorship_likely": True,
            "score": 0, "score_reason": "",
        }]

    return all_jobs[:max_results]
