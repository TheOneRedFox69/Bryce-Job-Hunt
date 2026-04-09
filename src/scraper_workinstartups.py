import time, random, logging, requests
from bs4 import BeautifulSoup
logger = logging.getLogger(__name__)
_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-GB,en;q=0.9"}
_TERMS = ["chief of staff", "head of operations", "commercial lead", "business development", "coo"]
def _fetch(url, retries=3):
    session = requests.Session()
    session.headers.update(_HEADERS)
    for i in range(retries):
        try:
            time.sleep(random.uniform(1.5, 3.5) + i * 2)
            r = session.get(url, timeout=15)
            if r.status_code == 200: return r.text
        except Exception as e: logger.debug(f"WorkInStartups fetch error: {e}")
    return None
def _parse(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    cards = soup.select("div.job, article.job, div[class*='job-item'], li.job-listing, div[class*='vacancy'], div.card, article.listing")
    for card in cards:
        try:
            title_el = card.select_one("h2, h3, h4, [class*='title']")
            company_el = card.select_one("[class*='company'], [class*='employer']")
            loc_el = card.select_one("[class*='location']")
            salary_el = card.select_one("[class*='salary']")
            link_el = card.select_one("a")
            if not title_el: continue
            href = ""
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("/"): href = f"https://workinstartups.com{href}"
            jobs.append({"title": title_el.get_text(strip=True), "company": company_el.get_text(strip=True) if company_el else "Unknown", "location": loc_el.get_text(strip=True) if loc_el else "UK", "salary": salary_el.get_text(strip=True) if salary_el else None, "url": href or "https://workinstartups.com/job-board", "summary": "", "tags": ["WorkInStartups", "UK Startup"], "match_tags": [], "posted_date": None, "source": "WorkInStartups", "sponsorship_likely": True, "score": 0, "score_reason": ""})
        except Exception as e: logger.debug(f"WorkInStartups parse error: {e}")
    return jobs
def scrape_workinstartups(max_results=20):
    all_jobs = []
    for term in _TERMS[:4]:
        html = _fetch(f"https://workinstartups.com/job-board/search/{requests.utils.quote(term)}/")
        if html: all_jobs.extend(_parse(html))
    if not all_jobs:
        return [{"title": "WorkInStartups — job search", "company": "Browse on WorkInStartups", "location": "UK", "salary": None, "url": "https://workinstartups.com/job-board/search/chief-of-staff/", "summary": "WorkInStartups scraper returned no results. Click to browse directly.", "tags": ["WorkInStartups"], "match_tags": [], "posted_date": None, "source": "WorkInStartups", "sponsorship_likely": True, "score": 0, "score_reason": ""}]
    return all_jobs[:max_results]