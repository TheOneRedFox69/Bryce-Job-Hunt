import time, random, logging, requests
from bs4 import BeautifulSoup
logger = logging.getLogger(__name__)
_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]
def _session():
    s = requests.Session()
    s.headers.update({"User-Agent": random.choice(_USER_AGENTS), "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"})
    return s
def _fetch(session, url, retries=3):
    for i in range(retries):
        try:
            time.sleep(random.uniform(2, 4) + i * 2)
            r = session.get(url, timeout=15)
            if r.status_code == 200: return r.text
            if r.status_code == 429: time.sleep(15 * (i + 1))
        except Exception as e: logger.debug(f"Wellfound fetch error: {e}")
    return None
def _parse(html, location):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    cards = soup.select("div[class*='JobListing'], div[class*='job-listing'], article[class*='job']")
    for card in cards:
        try:
            title_el = card.select_one("a[class*='title'], h2, h3")
            company_el = card.select_one("[class*='company']")
            loc_el = card.select_one("[class*='location']")
            salary_el = card.select_one("[class*='salary'], [class*='compensation']")
            link_el = card.select_one("a[href*='/jobs/']")
            if not title_el: continue
            href = ""
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("/"): href = f"https://wellfound.com{href}"
            jobs.append({"title": title_el.get_text(strip=True), "company": company_el.get_text(strip=True) if company_el else "Unknown", "location": loc_el.get_text(strip=True) if loc_el else location, "salary": salary_el.get_text(strip=True) if salary_el else None, "url": href or "https://wellfound.com/jobs", "summary": "", "tags": ["Wellfound", "Startup"], "match_tags": [], "posted_date": None, "source": "Wellfound", "sponsorship_likely": None, "score": 0, "score_reason": ""})
        except Exception as e: logger.debug(f"Wellfound card error: {e}")
    return jobs
def scrape_wellfound(max_results=30):
    session = _session()
    all_jobs = []
    for role_slug, loc_slug in [("chief-of-staff","london"),("operations","london"),("business-development","london"),("chief-of-staff","amsterdam"),("operations","amsterdam")]:
        url = f"https://wellfound.com/jobs?role={role_slug}&location={loc_slug}&stage[]=series-a&stage[]=series-b&stage[]=seed"
        html = _fetch(session, url)
        if html: all_jobs.extend(_parse(html, loc_slug.title()))
        if len(all_jobs) >= max_results: break
    if not all_jobs:
        all_jobs = [{"title": "Wellfound — startup jobs search", "company": "Browse on Wellfound", "location": "London / Amsterdam", "salary": None, "url": "https://wellfound.com/jobs?role=chief-of-staff&location=london", "summary": "Wellfound scraper returned no results. Click to browse directly.", "tags": ["Wellfound", "Startup"], "match_tags": [], "posted_date": None, "source": "Wellfound", "sponsorship_likely": None, "score": 0, "score_reason": ""}]
    return all_jobs[:max_results]