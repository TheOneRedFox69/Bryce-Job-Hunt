"""
Scores and deduplicates job listings against Bryce's profile.
Scoring is rule-based (fast, no API cost) with keyword matching.
"""

import re
from urllib.parse import urlparse


def score_jobs(jobs: list[dict], profile: dict) -> list[dict]:
    """
    Score a list of jobs against the candidate profile.
    Deduplicates by URL, scores each, sorts by score descending.
    """
    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for job in jobs:
        url = _normalise_url(job.get("url", ""))
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(job)
        elif not url:
            unique.append(job)  # Keep jobs without URLs

    # Score each
    scored = [_score_job(job, profile) for job in unique]

    # Sort by score descending
    scored.sort(key=lambda j: j.get("score", 0), reverse=True)
    return scored


def _normalise_url(url: str) -> str:
    """Strip query params for deduplication."""
    try:
        parsed = urlparse(url)
        return f"{parsed.netloc}{parsed.path}".lower().rstrip("/")
    except Exception:
        return url.lower()


def _score_job(job: dict, profile: dict) -> dict:
    weights = profile.get("scoring_weights", {})
    reasons = []
    total = 0

    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()
    summary = (job.get("summary") or "").lower()
    location = (job.get("location") or "").lower()
    salary_str = (job.get("salary") or "").lower()
    full_text = f"{title} {summary} {' '.join(job.get('tags', []))}".lower()

    # ── Role match (30 pts) ────────────────────────────────────────────────────
    role_score = 0
    target_roles_lower = [r.lower() for r in profile.get("target_roles", [])]
    role_keywords = {
        "chief of staff": ["chief of staff", "cos"],
        "commercial": ["commercial lead", "head of commercial", "commercial director", "vp commercial"],
        "coo": ["coo", "chief operating", "head of operations", "vp operations", "vp of operations"],
        "operations": ["operations manager", "head of ops", "operations lead", "director of operations"],
        "general manager": ["general manager", "gm"],
        "business development": ["business development", "bd lead", "head of bd", "vp bd"],
    }
    matched_role = None
    for category, variants in role_keywords.items():
        if any(v in title for v in variants):
            role_score = weights.get("role_match", 30)
            matched_role = category
            break
    if role_score == 0 and any(v in title for v in ["director", "head of", "lead", "manager"]):
        role_score = int(weights.get("role_match", 30) * 0.5)
        matched_role = "adjacent leadership"

    total += role_score
    if matched_role:
        reasons.append(f"Strong role match ({matched_role})")
    elif role_score > 0:
        reasons.append("Partial role match")

    # ── Sector match (20 pts) ──────────────────────────────────────────────────
    sector_score = 0
    sector_keywords = {
        "medtech": ["medtech", "medical device", "medical technology", "healthcare technology"],
        "healthtech": ["healthtech", "digital health", "health tech", "health technology"],
        "life sciences": ["life sciences", "life science", "biopharma", "biotech", "pharmaceutical"],
        "deep tech": ["deep tech", "deeptech", "hard tech", "hardware", "frontier tech"],
        "agrifood": ["agrifood", "agri-food", "foodtech", "food tech", "agtech"],
        "climate": ["climate", "cleantech", "clean tech", "sustainability", "net zero"],
        "saas": ["saas", "software", "b2b", "enterprise software"],
    }
    matched_sector = None
    priority_sectors = ["medtech", "healthtech", "life sciences", "deep tech"]
    for sector, variants in sector_keywords.items():
        if any(v in full_text for v in variants):
            if sector in priority_sectors:
                sector_score = weights.get("sector_match", 20)
            else:
                sector_score = int(weights.get("sector_match", 20) * 0.6)
            matched_sector = sector
            break

    # Bonus if "startup" or early-stage signals present
    if any(w in full_text for w in ["startup", "start-up", "scale-up", "scaleup", "early-stage"]):
        sector_score = min(sector_score + 5, weights.get("sector_match", 20))

    total += sector_score
    if matched_sector:
        reasons.append(f"Sector fit: {matched_sector}")

    # ── Location match (15 pts) ────────────────────────────────────────────────
    location_score = 0
    target_locations_lower = [l.lower() for l in profile.get("target_locations", [])]
    for loc in target_locations_lower:
        if loc in location:
            location_score = weights.get("location_match", 15)
            break
    # Partial: remote or hybrid
    if location_score == 0 and any(w in location for w in ["remote", "hybrid", "flexible"]):
        location_score = int(weights.get("location_match", 15) * 0.5)

    total += location_score
    if location_score == weights.get("location_match", 15):
        reasons.append(f"Location match")
    elif location_score > 0:
        reasons.append("Remote/hybrid option")

    # ── Stage match (10 pts) ───────────────────────────────────────────────────
    stage_score = 0
    stage_keywords = {
        "series a": ["series a", "series-a"],
        "series b": ["series b", "series-b"],
        "seed": ["seed stage", "seed-stage", "seed funded"],
        "early": ["early stage", "early-stage", "pre-seed"],
        "growth": ["growth stage", "scale-up", "scaleup"],
    }
    for stage, variants in stage_keywords.items():
        if any(v in full_text for v in variants):
            stage_score = weights.get("stage_match", 10)
            break

    total += stage_score
    if stage_score > 0:
        reasons.append("Startup stage match")

    # ── Salary match (10 pts) ──────────────────────────────────────────────────
    salary_score = 0
    salary_min = profile.get("target_salary_min_gbp", 80000)
    salary_max = profile.get("target_salary_max_gbp", 110000)

    if salary_str:
        nums = re.findall(r"[\d,]+", salary_str.replace("£", "").replace("$", "").replace("€", ""))
        nums = [int(n.replace(",", "")) for n in nums if len(n.replace(",", "")) >= 4]
        if nums:
            listed_mid = sum(nums) / len(nums)
            # Convert EUR/USD rough parity (close enough for matching)
            if "€" in salary_str or "eur" in salary_str:
                listed_mid *= 0.86
            elif "$" in salary_str and "us" in salary_str.lower():
                listed_mid *= 0.79
            if salary_min <= listed_mid <= salary_max * 1.2:
                salary_score = weights.get("salary_match", 10)
            elif listed_mid >= salary_min * 0.85:
                salary_score = int(weights.get("salary_match", 10) * 0.5)
    else:
        # No salary listed — neutral (half points)
        salary_score = int(weights.get("salary_match", 10) * 0.5)

    total += salary_score

    # ── Sponsorship likely (10 pts) ────────────────────────────────────────────
    sponsorship_score = 0
    sponsorship_likely = job.get("sponsorship_likely")

    if sponsorship_likely is True:
        sponsorship_score = weights.get("sponsorship_likely", 10)
    elif sponsorship_likely is None:
        # Infer from location: UK/EU companies generally able to sponsor
        if any(loc in location for loc in ["london", "uk", "amsterdam", "netherlands", "paris", "france",
                                            "berlin", "germany", "stockholm", "sweden", "copenhagen"]):
            sponsorship_score = int(weights.get("sponsorship_likely", 10) * 0.7)
        elif "canada" in location or "toronto" in location:
            sponsorship_score = int(weights.get("sponsorship_likely", 10) * 0.6)

    total += sponsorship_score
    if sponsorship_score >= weights.get("sponsorship_likely", 10) * 0.7:
        reasons.append("Sponsorship likely")

    # ── Skills match (5 pts) ───────────────────────────────────────────────────
    skills_score = 0
    candidate_skills = [s.lower() for s in profile.get("skills_keywords", [])]
    matches = [s for s in candidate_skills if s in full_text]
    match_tags = [m.title() for m in matches[:3]]

    if len(matches) >= 5:
        skills_score = weights.get("skills_match", 5)
    elif len(matches) >= 3:
        skills_score = int(weights.get("skills_match", 5) * 0.7)
    elif len(matches) >= 1:
        skills_score = int(weights.get("skills_match", 5) * 0.4)

    total += skills_score
    if match_tags:
        reasons.append(f"Skills: {', '.join(match_tags[:3])}")

    # ── Penalties ─────────────────────────────────────────────────────────────
    penalty = 0
    avoid_keywords = [
        "investment analyst", "venture capital associate", "vc analyst",
        "software engineer", "developer", "devops", "data scientist",
        "consultant", "accounting", "finance manager",
    ]
    for kw in avoid_keywords:
        if kw in title:
            penalty += 15
            reasons.append(f"⚠ Penalised: '{kw}' in title")
            break

    total = max(0, min(100, total - penalty))

    # Update job
    job["score"] = total
    job["score_reason"] = ". ".join(reasons) if reasons else "Low match — limited overlap with profile."
    job["match_tags"] = match_tags

    return job
