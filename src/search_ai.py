"""
AI job search using the Anthropic API with the web_search tool.
Returns structured job listings from live web results.
"""

import json
import os
import anthropic

_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set. Add it to Streamlit secrets or your environment.")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def ai_job_search(role: str, location: str, sector: str) -> list[dict]:
    """
    Search the web for live job listings using Claude + web_search tool.
    Returns a list of normalised job dicts.
    """
    client = _get_client()

    prompt = f"""You are a job search assistant. Search the web for current, live job postings.

SEARCH REQUEST:
- Role: {role}
- Location: {location}
- Sector: {sector}

Search for real, currently open job listings matching these criteria. Find 6–10 results from 
sources like LinkedIn, Indeed, Glassdoor, company career pages, and job boards.

Return ONLY a valid JSON array (no markdown, no preamble, no explanation).
Each object must have these exact keys:
{{
  "title": "exact job title from the listing",
  "company": "company name",
  "location": "city/country",
  "salary": "salary range if listed, else null",
  "url": "direct URL to the job listing",
  "summary": "2-3 sentence description of the role and what the company does",
  "tags": ["array", "of", "4-6", "relevant", "tags"],
  "match_tags": ["2-3 tags matching the candidate's VC/MedTech/commercial background"],
  "posted_date": "when posted if available, else null",
  "source": "LinkedIn|Indeed|Glassdoor|Company|Other",
  "sponsorship_likely": true/false
}}

Return ONLY the JSON array. No other text."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract text blocks from response (web search results are embedded)
    raw_text = ""
    for block in response.content:
        if block.type == "text":
            raw_text += block.text

    return _parse_jobs(raw_text, source_label="AI Search")


def _parse_jobs(raw: str, source_label: str = "AI Search") -> list[dict]:
    """Parse JSON array from AI response, handling markdown fences."""
    try:
        cleaned = raw.strip()
        # Strip markdown code fences if present
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        # Find the JSON array
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start == -1 or end == 0:
            return []
        jobs = json.loads(cleaned[start:end])
        # Normalise
        normalised = []
        for j in jobs:
            if not isinstance(j, dict):
                continue
            j.setdefault("source", source_label)
            j.setdefault("score", 0)
            j.setdefault("score_reason", "")
            j.setdefault("salary", None)
            j.setdefault("posted_date", None)
            j.setdefault("tags", [])
            j.setdefault("match_tags", [])
            j.setdefault("sponsorship_likely", None)
            normalised.append(j)
        return normalised
    except Exception:
        return []
