"""
Company discovery engine.

Step 1: Use Claude + web search to find Series A/B startups in target sectors/locations.
Step 2: For each company found, search for their open roles directly.

This surfaces roles that never make it to job boards — particularly relevant for
small (15-50 person) startups who post only on their own careers pages.
"""

import json
import os
import logging
import anthropic

logger = logging.getLogger(__name__)

_client = None

# Target company profiles to search for
_COMPANY_SEARCHES = [
    "Series A MedTech startup London hiring 2025",
    "Series B HealthTech startup London careers 2025",
    "Series A deep tech startup London jobs 2025",
    "Series A biotech startup London hiring 2025",
    "Series A startup Amsterdam chief of staff jobs 2025",
    "Series B startup London head of operations hiring 2025",
    "MedTech startup London 15-50 employees hiring commercial 2025",
    "VC backed startup London chief of staff role 2025",
    "Index Ventures Atomico portfolio company London hiring 2025",
    "Balderton General Catalyst portfolio startup London jobs 2025",
]


def _get_client():
    global _client
    if _client is None:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not set.")
        _client = anthropic.Anthropic(api_key=key)
    return _client


def _parse_jobs(raw: str) -> list[dict]:
    try:
        cleaned = raw.strip()
        if "```" in cleaned:
            parts = cleaned.split("```")
            for part in parts:
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
        normalised = []
        for j in jobs:
            if not isinstance(j, dict) or not j.get("title"):
                continue
            j.setdefault("source",             "Company Career Page")
            j.setdefault("score",              0)
            j.setdefault("score_reason",       "")
            j.setdefault("salary",             None)
            j.setdefault("posted_date",        None)
            j.setdefault("tags",               [])
            j.setdefault("match_tags",         [])
            j.setdefault("sponsorship_likely", True)
            j.setdefault("company_size",       None)
            j.setdefault("stage",              None)
            j.setdefault("vc_backed",          None)
            normalised.append(j)
        return normalised
    except Exception:
        return []


def discover_company_roles(num_queries: int = 5) -> list[dict]:
    """
    Find startups matching Bryce's criteria and check their careers pages.
    
    Args:
        num_queries: Number of company discovery searches to run.
    
    Returns:
        List of job dicts from company careers pages.
    """
    client = _get_client()
    all_jobs = []
    seen = set()

    queries = _COMPANY_SEARCHES[:num_queries]

    for query in queries:
        prompt = f"""Search the web for: "{query}"

Find real startups matching this search. For each company found, also search for their 
current open job listings — specifically looking for roles like:
Chief of Staff, Head of Operations, Commercial Lead, COO, General Manager, 
Head of Business Development, Head of Partnerships, Head of Growth, Country Manager.

Return ONLY a valid JSON array. Each object:
{{
  "title": "exact job title",
  "company": "company name",
  "location": "city, country",
  "salary": null or "salary range if found",
  "url": "direct link to the job listing or company careers page",
  "summary": "2-3 sentences about the role and what the company does",
  "tags": ["relevant", "tags", "including", "sector"],
  "match_tags": [],
  "posted_date": null,
  "source": "Company Career Page",
  "sponsorship_likely": true,
  "company_size": "estimated headcount if known",
  "stage": "Series A or Series B or Seed etc if known",
  "vc_backed": true,
  "score": 0,
  "score_reason": ""
}}

Only include roles that are currently open. If a company has no open relevant roles, skip it.
Return ONLY the JSON array, no other text."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": prompt}],
            )

            raw = ""
            for block in response.content:
                if block.type == "text":
                    raw += block.text

            jobs = _parse_jobs(raw)
            for job in jobs:
                key = f"{job.get('title','')}|{job.get('company','')}".lower()
                if key not in seen:
                    seen.add(key)
                    all_jobs.append(job)

        except Exception as e:
            logger.warning(f"Company discovery error for '{query}': {e}")
            continue

    return all_jobs
