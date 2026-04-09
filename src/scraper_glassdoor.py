import time, random, logging, requests
from bs4 import BeautifulSoup
logger = logging.getLogger(__name__)
_USER_AGENTS = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"]
_QUERIES = [("Chief of Staff", "London, UK"), ("Head of Operations", "London, UK"), ("Commercial Lead", "London, UK"), ("Chief of Staff", "Amsterdam, Netherlands"), ("COO startup", "London, UK")]
def _session():
    s = requests.Session()
    s.headers.update({"User-Agent": random.choice(_USER_AGENTS), "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"})
    return s
def _fetch(session, url, retries=3):
    for i in range(retries):
        try:
            time.sleep(random.uniform(2, 5) + i * 3)
            r = session.get(url, timeout=15)
            if r.status_code == 200: return r.text
            if r.status_code == 429: time.sleep(20 * (i + 1))
        except Exception as e: logger.debug(f"Glassdoor fetch error: {e}")
    return None
def _parse(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    cards = soup.select("li[data-test='jobListing'], div[class*='jobCard'], article[class*='JobCard']")
    for card in cards:
        try:
            title_el = card.select_one("[data-test='job-title'], [class*='JobTitle'], h2, h3")
            company_el = card.select_one("[data-test='employer-name'], [class*='EmployerName']")
            loc_el = card.select_one("[data-test='emp-location'], [class*='location']")
            salary_el = card.select_one("[data-test='detailSalary'], [class*='salary']")
            link_el = card.select_one("a[data-test='job-title'], a[href*='/job-listing/']")
            if not title_el: continue
            href = ""
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("/"): href = f"https://www.glassdoor.com{href}"
            jobs.append({"title": title_el.get_text(strip=True), "company": company_el.get_text(strip=True) if company_el else "Unknown", "location": loc_el.get_text(strip=True) if loc_el else "", "salary": salary_el.get_text(strip=True) if salary_el else None, "url": href or "https://www.glassdoor.com/Job/index.htm", "summary": "", "tags": ["Glassdoor"], "match_tags": [], "posted_date": None, "source": "Glassdoor", "sponsorship_likely": None, "score": 0, "score_reason": ""})
        except Exception as e: logger.debug(f"Glassdoor card error: {e}")
    return jobs
def scrape_glassdoor(max_results=30):
    session = _session()
    all_jobs = []
    for role, location in _QUERIES[:3]:
        url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={requests.utils.quote(role)}&locT=C&locKeyword={requests.utils.quote(location)}&fromAge=30"
        html = _fetch(session, url)
        if html: all_jobs.extend(_parse(html))
    if not all_jobs:
        return [{"title": "Glassdoor — job search", "company": "Browse on Glassdoor", "location": "London, UK", "salary": None, "url": "https://www.glassdoor.com/Job/london-chief-of-staff-jobs-SRCH_IL.0,6_IC2671300_KO7,21.htm", "summary": "Glassdoor scraper returned no results. Click to browse directly.", "tags": ["Glassdoor"], "match_tags": [], "posted_date": None, "source": "Glassdoor", "sponsorship_likely": None, "score": 0, "score_reason": ""}]
    return all_jobs[:max_results]