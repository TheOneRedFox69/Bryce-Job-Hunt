import time, random, logging, requests
from bs4 import BeautifulSoup
logger = logging.getLogger(__name__)
_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-GB,en;q=0.9"}
_QUERIES = ["chief of staff", "head of operations", "commercial lead", "chief operating officer"]
def _fetch(url, retries=3):
    session = requests.Session()
    session.headers.update(_HEADERS)
    for i in range(retries):
        try:
            time.sleep(random.uniform(2, 4) + i * 2)
            r = session.get(url, timeout=15)
            if r.status_code == 200: return r.text
            if r.status_code == 429: time.sleep(20 * (i + 1))
        except Exception as e: logger.debug(f"Otta fetch error: {e}")
    return None
def _parse(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    cards = soup.select("div[class*='JobCard'], article[class*='job'], div[class*='job-card']")
    for card in cards:
        try:
            title_el = card.select_one("h2, h3, [class*='title']")
            company_el = card.select_one("[class*='company'], [class*='employer']")
            loc_el = card.select_one("[class*='location']")
            salary_el = card.select_one("[class*='salary']")
            link_el = card.select_one("a")
            if not title_el: continue
            href = ""
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("/"): href = f"https://app.otta.com{href}"
            jobs.append({"title": title_el.get_text(strip=True), "company": company_el.get_text(strip=True) if company_el else "Unknown", "location": loc_el.get_text(strip=True) if loc_el else "London", "salary": salary_el.get_text(strip=True) if salary_el else None, "url": href or "https://app.otta.com/jobs", "summary": "", "tags": ["Otta", "Startup", "London"], "match_tags": [], "posted_date": None, "source": "Otta", "sponsorship_likely": True, "score": 0, "score_reason": ""})
        except Exception as e: logger.debug(f"Otta parse error: {e}")
    return jobs
def scrape_otta(max_results=30):
    all_jobs = []
    for query in _QUERIES:
        html = _fetch(f"https://app.otta.com/jobs?search={requests.utils.quote(query)}")
        if html: all_jobs.extend(_parse(html))
    if not all_jobs:
        return [{"title": "Otta — startup jobs search", "company": "Browse on Otta", "location": "London, UK", "salary": None, "url": "https://app.otta.com/jobs?search=chief+of+staff", "summary": "Otta scraper returned no results. Click to browse directly.", "tags": ["Otta", "Startup"], "match_tags": [], "posted_date": None, "source": "Otta", "sponsorship_likely": True, "score": 0, "score_reason": ""}]
    return all_jobs[:max_results]