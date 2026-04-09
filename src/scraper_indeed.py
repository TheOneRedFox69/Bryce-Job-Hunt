"""
Indeed job scraper using their public search endpoint.
Indeed is more scraper-tolerant than LinkedIn but still rate-limits aggressively.
"""

import time
import random
import logging
import re
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

# Indeed country domains
_INDEED_DOMAINS = {
    "uk": "uk.indeed.com",
    "london": "uk.indeed.com",
    "amsterdam": "indeed.com",
    "netherlands": "indeed.com",
    "paris": "fr.indeed.com",
    "france": "fr.indeed.com",
    "toronto": "ca.indeed.com",
    "canada": "ca.indeed.com",
    "stockholm": "se.indeed.com",
    "sweden": "se.indeed.com",
    "copenhagen": "dk.indeed.com",
    "denmark": "dk.indeed.com",
    "berlin": "de.indeed.com",
    "germany": "de.indeed.com",
}


def _get_domain(location: str) -> str:
    key = location.lower().split(",")[0].strip()
    return _INDEED_DOMAINS.get(key, "uk.indeed.com")


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "DNT": "1",
    })
    return session


def _fetch(session: requests.Session, url: str) -> str | None:
    for attempt in range(3):
        try:
            time.sleep(random.uniform(1.5, 3.0) + attempt * 2)
            resp = session.get(url, timeout=15)
            if resp.status_code == 429:
                time.sleep(15 * (attempt + 1))
                continue
            if resp.status_code != 200:
                return None
            return resp.text
        except requests.RequestException as e:
            logger.warning(f"Indeed fetch error: {e}")
    return None


def _parse_indeed_page(html: str, domain: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # Indeed uses td.resultContent or div.job_seen_beacon
    cards = soup.select("div.job_seen_beacon, td.resultContent")

    for card in cards:
        try:
            title_el = card.select_one("h2.jobTitle span[title], h2.jobTitle a")
            company_el = card.select_one("span.companyName, [data-testid='company-name']")
            location_el = card.select_one("div.companyLocation, [data-testid='text-location']")
            salary_el = card.select_one("div.salary-snippet-container, div.attribute_snippet")
            link_el = card.select_one("h2.jobTitle a")
            date_el = card.select_one("span.date")

            if not title_el or not link_el:
                continue

            href = link_el.get("href", "")
            if href.startswith("/"):
                href = f"https://{domain}{href}"

            # Extract job key for deduplication
            jk_match = re.search(r"jk=([a-f0-9]+)", href)
            job_key = jk_match.group(1) if jk_match else href

            summary_el = card.select_one("div.job-snippet, ul.job-snippet")
            summary = summary_el.get_text(separator=" ", strip=True) if summary_el else ""

            jobs.append({
                "title": title_el.get("title") or title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "Unknown",
                "location": location_el.get_text(strip=True) if location_el else "",
                "url": href,
                "posted_date": date_el.get_text(strip=True) if date_el else None,
                "salary": salary_el.get_text(strip=True) if salary_el else None,
                "source": "Indeed",
                "summary": summary,
                "tags": [],
                "match_tags": [],
                "score": 0,
                "score_reason": "",
                "sponsorship_likely": None,
                "_job_key": job_key,
            })
        except Exception as e:
            logger.debug(f"Indeed card parse error: {e}")
            continue

    return jobs


def scrape_indeed(role: str, location: str, max_results: int = 15) -> list[dict]:
    """
    Scrape Indeed for job listings.

    Args:
        role: Job title / keyword
        location: City/country
        max_results: Max listings to return

    Returns:
        List of normalised job dicts
    """
    session = _build_session()
    domain = _get_domain(location)

    # Location string for Indeed (use just the city part)
    loc_for_indeed = location.split(",")[0].strip()

    params = {
        "q": role,
        "l": loc_for_indeed,
        "sort": "date",
        "fromage": "30",   # Past 30 days
        "limit": "25",
        "lang": "en",
    }
    query_string = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
    search_url = f"https://{domain}/jobs?{query_string}"

    logger.info(f"Indeed search: {search_url}")

    html = _fetch(session, search_url)
    if not html:
        logger.warning("Indeed fetch failed.")
        return _fallback_indeed_links(role, location, domain)

    jobs = _parse_indeed_page(html, domain)
    logger.info(f"Indeed: parsed {len(jobs)} jobs")

    if not jobs:
        return _fallback_indeed_links(role, location, domain)

    # Deduplicate by job key
    seen = set()
    deduped = []
    for j in jobs:
        key = j.pop("_job_key", j["url"])
        if key not in seen:
            seen.add(key)
            deduped.append(j)

    return deduped[:max_results]


def _fallback_indeed_links(role: str, location: str, domain: str) -> list[dict]:
    encoded_role = requests.utils.quote(role)
    encoded_loc = requests.utils.quote(location.split(",")[0].strip())
    url = f"https://{domain}/jobs?q={encoded_role}&l={encoded_loc}&sort=date&fromage=30"
    return [{
        "title": f"{role} — Indeed search",
        "company": "Browse on Indeed",
        "location": location,
        "url": url,
        "posted_date": None,
        "salary": None,
        "source": "Indeed",
        "summary": "Indeed scraper returned no results. Click to browse directly.",
        "tags": ["Indeed", role],
        "match_tags": [],
        "score": 0,
        "score_reason": "Manual review required.",
        "sponsorship_likely": None,
    }]
