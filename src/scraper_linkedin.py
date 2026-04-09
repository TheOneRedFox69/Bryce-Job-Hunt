"""
LinkedIn job scraper.

⚠️  WARNING: Scraping LinkedIn violates their Terms of Service (Section 8.2).
    Use at your own risk. This scraper uses the public LinkedIn Jobs search
    endpoint which does not require authentication. LinkedIn actively blocks
    scrapers — expect frequent failures and IP rate limiting.

    Mitigation strategies implemented:
    - Randomised User-Agent rotation
    - Random delays between requests
    - Session reuse with cookie persistence
    - Retry logic with exponential backoff
    - Falls back gracefully on block/CAPTCHA detection

    For production use, consider:
    - Rotating residential proxies (e.g. Bright Data, Oxylabs)
    - A headless browser (Playwright/Selenium) for JS-rendered pages
    - The unofficial linkedin-jobs-scraper npm package via subprocess
"""

import time
import random
import logging
import re
from typing import Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── User-agent pool ───────────────────────────────────────────────────────────
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

# ── LinkedIn location GeoIDs (avoids ambiguous text matching) ─────────────────
_GEO_IDS = {
    "london":      "90009496",
    "uk":          "101165590",
    "amsterdam":   "102011674",
    "netherlands": "102890719",
    "paris":       "104246759",
    "france":      "105015875",
    "toronto":     "100025096",
    "canada":      "101174742",
    "stockholm":   "106167422",
    "sweden":      "105117694",
    "copenhagen":  "100991870",
    "denmark":     "104514075",
    "berlin":      "106967730",
    "germany":     "101282230",
}

# LinkedIn job type codes
_EXPERIENCE_LEVELS = "2,3,4"  # Associate, Mid-Senior, Director


def _get_geo_id(location: str) -> Optional[str]:
    key = location.lower().split(",")[0].strip()
    return _GEO_IDS.get(key)


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
    })
    return session


def _detect_block(html: str) -> bool:
    """Return True if LinkedIn returned a block/CAPTCHA page."""
    markers = [
        "authwall",
        "checkpoint/challenge",
        "we noticed some unusual activity",
        "please complete this security check",
        "captcha",
        "cf-browser-verification",
    ]
    lower = html.lower()
    return any(m in lower for m in markers)


def _fetch_with_retry(session: requests.Session, url: str, max_retries: int = 3) -> Optional[str]:
    """Fetch URL with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            # Random delay to mimic human behaviour
            time.sleep(random.uniform(1.5, 3.5) + attempt * 2)
            resp = session.get(url, timeout=15)
            if resp.status_code == 429:
                logger.warning(f"LinkedIn rate limit (429). Waiting {10 * (attempt+1)}s...")
                time.sleep(10 * (attempt + 1))
                continue
            if resp.status_code != 200:
                logger.warning(f"LinkedIn returned {resp.status_code} for {url}")
                return None
            if _detect_block(resp.text):
                logger.warning("LinkedIn block/CAPTCHA detected.")
                return None
            return resp.text
        except requests.RequestException as e:
            logger.warning(f"Request error (attempt {attempt+1}): {e}")
            time.sleep(5 * (attempt + 1))
    return None


def _parse_job_list_page(html: str) -> list[dict]:
    """Parse the LinkedIn Jobs search results page."""
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # LinkedIn public search uses <ul class="jobs-search__results-list">
    cards = soup.select("li.jobs-search__results-list > div.base-card")
    if not cards:
        # Fallback selector for alternate page structure
        cards = soup.select("div.base-card")

    for card in cards:
        try:
            title_el = card.select_one("h3.base-search-card__title, h3.job-result-card__title")
            company_el = card.select_one("h4.base-search-card__subtitle, h4.job-result-card__company")
            location_el = card.select_one("span.job-search-card__location, span.job-result-card__location")
            link_el = card.select_one("a.base-card__full-link, a.result-card__full-card-link")
            date_el = card.select_one("time")
            salary_el = card.select_one("span.job-search-card__salary-info")

            if not title_el or not link_el:
                continue

            jobs.append({
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "Unknown",
                "location": location_el.get_text(strip=True) if location_el else "",
                "url": link_el.get("href", "").split("?")[0],
                "posted_date": date_el.get("datetime") if date_el else None,
                "salary": salary_el.get_text(strip=True) if salary_el else None,
                "source": "LinkedIn",
                "summary": "",  # Enriched in detail fetch if needed
                "tags": [],
                "match_tags": [],
                "score": 0,
                "score_reason": "",
                "sponsorship_likely": True,  # LinkedIn listings often include sponsorship info
            })
        except Exception as e:
            logger.debug(f"Card parse error: {e}")
            continue

    return jobs


def _enrich_job_detail(session: requests.Session, job: dict) -> dict:
    """
    Optionally fetch the job detail page to extract description.
    Only called for top-scoring jobs to avoid excessive requests.
    """
    if not job.get("url"):
        return job
    html = _fetch_with_retry(session, job["url"], max_retries=2)
    if not html:
        return job
    soup = BeautifulSoup(html, "html.parser")
    desc_el = soup.select_one("div.show-more-less-html__markup, div.description__text")
    if desc_el:
        text = desc_el.get_text(separator=" ", strip=True)
        job["summary"] = text[:400] + "..." if len(text) > 400 else text
    return job


def scrape_linkedin(role: str, location: str, max_results: int = 15) -> list[dict]:
    """
    Scrape LinkedIn Jobs public search for a given role and location.

    Args:
        role: Job title / keyword (e.g. "Chief of Staff")
        location: City/country string (e.g. "London, UK")
        max_results: Max number of listings to return

    Returns:
        List of normalised job dicts
    """
    session = _build_session()

    # First warm up with a visit to linkedin.com to collect cookies
    warmup_html = _fetch_with_retry(session, "https://www.linkedin.com/jobs/", max_retries=2)
    if not warmup_html:
        logger.warning("LinkedIn warmup request failed — proceeding anyway.")

    # Build search URL
    geo_id = _get_geo_id(location)
    params = {
        "keywords": role,
        "location": location,
        "f_TPR": "r2592000",     # Posted in last 30 days
        "f_E": _EXPERIENCE_LEVELS,
        "position": "1",
        "pageNum": "0",
    }
    if geo_id:
        params["geoId"] = geo_id

    base_url = "https://www.linkedin.com/jobs/search/"
    query_string = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
    search_url = f"{base_url}?{query_string}"

    logger.info(f"LinkedIn search: {search_url}")

    html = _fetch_with_retry(session, search_url)
    if not html:
        logger.warning("LinkedIn search page fetch failed.")
        return _fallback_linkedin_links(role, location)

    jobs = _parse_job_list_page(html)
    logger.info(f"LinkedIn: parsed {len(jobs)} job cards")

    if not jobs:
        logger.warning("LinkedIn: no jobs parsed — page structure may have changed.")
        return _fallback_linkedin_links(role, location)

    # Trim to max_results
    jobs = jobs[:max_results]

    # Enrich top 3 with detail pages (to get summaries)
    for i, job in enumerate(jobs[:3]):
        time.sleep(random.uniform(2, 4))
        jobs[i] = _enrich_job_detail(session, job)

    return jobs


def _fallback_linkedin_links(role: str, location: str) -> list[dict]:
    """
    Return a single stub entry pointing to a LinkedIn search URL,
    so the user can at least click through and browse manually.
    """
    encoded_role = requests.utils.quote(role)
    encoded_loc = requests.utils.quote(location)
    search_url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={encoded_role}&location={encoded_loc}"
        f"&f_TPR=r2592000&f_E={_EXPERIENCE_LEVELS}"
    )
    return [{
        "title": f"{role} — LinkedIn search",
        "company": "Browse on LinkedIn",
        "location": location,
        "url": search_url,
        "posted_date": None,
        "salary": None,
        "source": "LinkedIn",
        "summary": (
            "LinkedIn scraper was blocked or returned no results. "
            "Click 'View listing' to open the LinkedIn search results directly in your browser."
        ),
        "tags": ["LinkedIn", role],
        "match_tags": [],
        "score": 0,
        "score_reason": "Manual review required — LinkedIn blocked automated access.",
        "sponsorship_likely": None,
    }]
