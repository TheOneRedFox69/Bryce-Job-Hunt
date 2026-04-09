import json, os, logging
import anthropic
logger = logging.getLogger(__name__)
_client = None
_SEARCHES = [
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
        if not key: raise ValueError("ANTHROPIC_API_KEY not set.")
        _client = anthropic.Anthropic(api_key=key)
    return _client
def _parse(raw):
    try:
        cleaned = raw.strip()
        if "```" in cleaned:
            for part in cleaned.split("```"):
                p = part.strip()
                if p.startswith("json"): p = p[4:]
                if p.startswith("["): cleaned = p; break
        start = cleaned.find("["); end = cleaned.rfind("]") + 1
        if start == -1 or end == 0: return []
        jobs = json.loads(cleaned[start:end])
        out = []
        for j in jobs:
            if not isinstance(j, dict) or not j.get("title"): continue
            j.setdefault("source", "Company Career Page"); j.setdefault("score", 0); j.setdefault("score_reason", ""); j.setdefault("salary", None); j.setdefault("posted_date", None); j.setdefault("tags", []); j.setdefault("match_tags", []); j.setdefault("sponsorship_likely", True); j.setdefault("company_size", None); j.setdefault("stage", None); j.setdefault("vc_backed", None)
            out.append(j)
        return out
    except Exception: return []
def discover_company_roles(num_queries=5):
    client = _get_client()
    all_jobs = []; seen = set()
    for query in _SEARCHES[:num_queries]:
        prompt = f"""Search the web for: "{query}"
Find startups matching this. For each, search for open roles: Chief of Staff, Head of Operations, Commercial Lead, COO, General Manager, Head of BD, Head of Partnerships, Head of Growth, Country Manager.
Return ONLY a valid JSON array. Each object: {{"title":"job title","company":"name","location":"city, country","salary":null,"url":"link to job or careers page","summary":"2-3 sentences about role and company","tags":["tags"],"match_tags":[],"posted_date":null,"source":"Company Career Page","sponsorship_likely":true,"company_size":"headcount if known","stage":"Series A/B/Seed etc","vc_backed":true,"score":0,"score_reason":""}}
Only include currently open roles. Return ONLY the JSON array."""
        try:
            response = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=3000, tools=[{"type": "web_search_20250305", "name": "web_search"}], messages=[{"role": "user", "content": prompt}])
            raw = "".join(b.text for b in response.content if b.type == "text")
            for job in _parse(raw):
                key = f"{job.get('title','')}|{job.get('company','')}".lower()
                if key not in seen: seen.add(key); all_jobs.append(job)
        except Exception as e: logger.warning(f"Company discovery error: {e}"); continue
    return all_jobs