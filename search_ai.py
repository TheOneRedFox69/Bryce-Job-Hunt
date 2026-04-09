"""
AI job search using Anthropic API + web_search tool.
Runs many varied queries across all target roles × locations.
Queries use different phrasing to maximise coverage across job boards.
"""

import json
import os
import logging
import anthropic

logger = logging.getLogger(__name__)

_client = None

# ── 30+ search queries covering all role × location combos ───────────────────
# Varied phrasing ensures different results from each query
_ALL_QUERIES = [
    # Chief of Staff — London
    ("Chief of Staff startup London",                       "London"),
    ("Chief of Staff Series A B London job",                "London"),
    ("CoS startup founder London hire 2025",                "London"),
    # COO / Head of Ops — London
    ("COO startup London Series A hiring",                  "London"),
    ("Head of Operations startup London job",               "London"),
    ("VP Operations early stage company London",            "London"),
    # Commercial / BD — London
    ("Head of Commercial startup London",                   "London"),
    ("Commercial Lead Series A London job",                 "London"),
    ("Head of Business Development startup London hire",    "London"),
    ("VP Business Development startup London 2025",         "London"),
    ("Head of Partnerships startup London",                 "London"),
    # GM / Growth — London
    ("General Manager startup London",                      "London"),
    ("Head of Growth startup London Series A",              "London"),
    ("Country Manager startup London",                      "London"),
    # MedTech / HealthTech specific — London
    ("Chief of Staff MedTech startup London",               "London"),
    ("Head of Operations HealthTech London",                "London"),
    ("Commercial Lead medical device startup London",       "London"),
    ("COO digital health startup London",                   "London"),
    # Amsterdam
    ("Chief of Staff startup Amsterdam",                    "Amsterdam"),
    ("Head of Operations startup Amsterdam",                "Amsterdam"),
    ("Commercial Lead startup Amsterdam",                   "Amsterdam"),
    ("COO Series A startup Amsterdam",                      "Amsterdam"),
    # Paris
    ("Chief of Staff startup Paris English",                "Paris"),
    ("Head of Operations startup Paris",                    "Paris"),
    # Toronto / Canada
    ("Chief of Staff startup Toronto",                      "Toronto"),
    ("Head of Operations startup Toronto",                  "Toronto"),
    ("Commercial Lead startup Canada",                      "Canada"),
    # Scandinavia
    ("Chief of Staff startup Stockholm",                    "Stockholm"),
    ("Head of Operations startup Copenhagen",               "Copenhagen"),
    ("Commercial Lead startup Scandinavia English",         "Scandinavia"),
    # Broad / multi-location
    ("Chief of Staff startup Europe English speaking",      "Europe"),
    ("Head of Commercial Series A startup Europe",          "Europe"),
    ("COO startup Europe English job 2025",                 "Europe"),
]

_SYSTEM_PROMPT = """You are a job search assistant finding real, currently open job listings.

CANDIDATE: Bryce Lowen — NZ citizen, relocating immediately. ~6 years experience.
VC Analyst background + Medical Device Sales (Fisher & Paykel Healthcare, 59% revenue growth).
Wants: Chief of Staff / Commercial Lead / COO / Head of Ops / GM at startup (15-50 people).
Target: Series A/B, MedTech/HealthTech/Deep Tech preferred, £80-110k, needs visa sponsorship.
Loves: CEO-facing, people leadership, top-tier VC-backed, science/tech founders.

Find ONLY real, currently open listings. Return JSON array only — no markdown, no preamble."""

_SCHEMA = """{
  "title": "exact job title",
  "company": "company name",
  "location": "city, country",
  "salary": "range or null",
  "url": "direct URL to listing",
  "summary": "2-3 sentences: role and company",
  "tags": ["4-6 tags"],
  "match_tags": [],
  "posted_date": "date or null",
  "source": "LinkedIn|Indeed|Glassdoor|Wellfound|Company|Other",
  "sponsorship_likely": true/false/null,
  "company_size": "headcount or null",
  "stage": "Seed|Series A|Series B|Series C|null",
  "vc_backed": true/false/null,
  "score": 0,
  "score_reason": ""
}"""


def _get_client():
    global _client
    if _client is None:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not set.")
        _client = anthropic.Anthropic(api_key=key)
    return _client


def _parse(raw: str) -> list[dict]:
    try:
        cleaned = raw.strip()
        if "```" in cleaned:
            for part in cleaned.split("```"):
                p = part.strip()
                if p.startswith("json"):
                    p = p[4:]
                if p.startswith("["):
                    cleaned = p
                    break
        start = cleaned.find("[")
        end   = cleaned.rfind("]") + 1
        if start == -1 or end == 0:
            return []
        jobs = json.loads(cleaned[start:end])
        out = []
        for j in jobs:
            if not isinstance(j, dict) or not j.get("title"):
                continue
            j.setdefault("source",             "AI Search")
            j.setdefault("score",              0)
            j.setdefault("score_reason",       "")
            j.setdefault("salary",             None)
            j.setdefault("posted_date",        None)
            j.setdefault("tags",               [])
            j.setdefault("match_tags",         [])
            j.setdefault("sponsorship_likely", None)
            j.setdefault("company_size",       None)
            j.setdefault("stage",              None)
            j.setdefault("vc_backed",          None)
            out.append(j)
        return out
    except Exception:
        return []


def ai_job_search(num_searches: int = 8) -> list[dict]:
    """
    Run num_searches queries from the full query matrix.
    Deduplicates by title+company.

    Args:
        num_searches: How many queries to run (max 34).
    Returns:
        List of normalised job dicts.
    """
    client = _get_client()
    queries = _ALL_QUERIES[:min(num_searches, len(_ALL_QUERIES))]
    all_jobs: list[dict] = []
    seen: set[str] = set()

    for role_kw, location in queries:
        prompt = f"""Search the web for currently open job listings.

QUERY: "{role_kw}" jobs in {location}

Find 4-6 real, live job postings matching this search. Focus on startups and scale-ups.
Return ONLY a valid JSON array using this schema per listing:
{_SCHEMA}

Return ONLY the JSON array. No other text."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                system=_SYSTEM_PROMPT,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": prompt}],
            )
            raw = "".join(b.text for b in response.content if b.type == "text")
            for job in _parse(raw):
                key = f"{job.get('title','')}|{job.get('company','')}".lower()
                if key not in seen:
                    seen.add(key)
                    all_jobs.append(job)
        except Exception as e:
            logger.warning(f"AI search error for '{role_kw}': {e}")
            continue

    return all_jobs
