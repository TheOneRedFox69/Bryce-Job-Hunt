"""
Scoring engine calibrated to Bryce's exact preferences:

Priority order:
  1. Role title & seniority         (28 pts)
  2. Salary match                   (18 pts)
  3. Mission & sector               (14 pts)
  4. Founding team quality signals  (10 pts)
  5. Equity / startup stage         ( 6 pts)
  6. Location match                 (12 pts)
  7. Sponsorship likelihood         ( 8 pts)
  8. Company size signal            ( 4 pts)

Bonuses:
  - CEO/founder-facing role         (+5)
  - People leadership required      (+5)
  - Top-tier VC backing             (+5)
  - Science/technical founders      (+3)
  - External representation role    (+3)
  - Commercial track record needed  (+3, medium weight)

Penalties:
  - Pure VC/investment analyst role (-20)
  - Large corporate signals         (-15)
  - Pure engineering/technical      (-15)
  - Consulting/agency               (-10)
"""

import re
from urllib.parse import urlparse


# ── Top-tier VC firm names for bonus detection ────────────────────────────────
TOP_TIER_VCS = {
    "sequoia", "a16z", "andreessen horowitz", "index ventures", "atomico",
    "accel", "benchmark", "general catalyst", "bessemer", "lightspeed",
    "tiger global", "softbank", "insight partners", "balderton", "notion capital",
    "true ventures", "firstmark", "spark capital", "greylock", "kleiner perkins",
    "founders fund", "union square ventures", "usv", "ycombinator", "y combinator",
    "techstars", "500 startups", "hoxton ventures", "episode 1", "octopus ventures",
}

SCIENCE_FOUNDER_SIGNALS = {
    "phd founded", "founder phd", "scientist founded", "deep tech",
    "spinout", "spin-out", "university spinout", "research commercialisation",
    "research commercialization", "lab", "professor", "academic founder",
    "ip-rich", "patent", "peer-reviewed", "clinical trial",
}


def score_jobs(jobs: list[dict], profile: dict) -> list[dict]:
    """Score, deduplicate, and sort jobs against Bryce's profile."""
    # Deduplicate by normalised URL
    seen, unique = set(), []
    for job in jobs:
        key = _norm_url(job.get("url", ""))
        if key not in seen:
            seen.add(key)
            unique.append(job)

    scored = [_score(job, profile) for job in unique]
    scored.sort(key=lambda j: j.get("score", 0), reverse=True)
    return scored


def _norm_url(url: str) -> str:
    try:
        p = urlparse(url)
        return f"{p.netloc}{p.path}".lower().rstrip("/")
    except Exception:
        return url.lower()


def _score(job: dict, profile: dict) -> dict:
    w = profile["scoring_weights"]
    reasons, bonuses, penalties = [], [], []
    total = 0

    title   = (job.get("title")   or "").lower()
    company = (job.get("company") or "").lower()
    summary = (job.get("summary") or "").lower()
    location = (job.get("location") or "").lower()
    salary_str = (job.get("salary") or "").lower()
    tags_text = " ".join(job.get("tags", [])).lower()
    full = f"{title} {summary} {tags_text} {company}"

    # ── 1. Role match (28 pts) ────────────────────────────────────────────────
    role_score = 0
    role_tiers = {
        # Tier A — perfect fit (full points)
        "tier_a": [
            "chief of staff", "cos",
            "commercial lead", "head of commercial", "vp commercial", "vp of commercial",
            "director of commercial",
            "coo", "chief operating officer",
            "head of operations", "vp operations", "vp of operations",
            "director of operations",
            "general manager", "gm",
            "country manager",
            "head of growth", "vp growth",
            "head of bd", "head of business development",
            "vp business development", "vp of business development",
            "head of partnerships", "vp partnerships",
            "investor relations", "head of investor relations",
        ],
        # Tier B — good fit (75%)
        "tier_b": [
            "operations manager", "commercial manager",
            "business development manager", "bd manager",
            "partnerships manager", "growth manager",
            "chief of staff", "strategy manager",
            "head of strategy",
        ],
        # Tier C — adjacent (40%)
        "tier_c": [
            "director", "head of", "lead", "manager",
            "senior manager",
        ],
    }

    matched_tier = None
    for variant in role_tiers["tier_a"]:
        if variant in title:
            role_score = w["role_match"]
            matched_tier = "A"
            break
    if not matched_tier:
        for variant in role_tiers["tier_b"]:
            if variant in title:
                role_score = int(w["role_match"] * 0.75)
                matched_tier = "B"
                break
    if not matched_tier:
        for variant in role_tiers["tier_c"]:
            if variant in title:
                role_score = int(w["role_match"] * 0.40)
                matched_tier = "C"
                break

    total += role_score
    if matched_tier == "A":
        reasons.append(f"Strong role match: {title.title()}")
    elif matched_tier == "B":
        reasons.append(f"Good role match: {title.title()}")
    elif matched_tier == "C":
        reasons.append("Adjacent leadership role")

    # ── 2. Salary match (18 pts) ──────────────────────────────────────────────
    sal_score = 0
    if not salary_str:
        # No salary listed — assume in range (no penalty per preferences)
        sal_score = int(w["salary_match"] * 0.8)
    else:
        nums = re.findall(r"[\d,]+", salary_str)
        nums = [int(n.replace(",", "")) for n in nums if 4 <= len(n.replace(",", "")) <= 7]
        if nums:
            mid = sum(nums) / len(nums)
            # Currency conversion to GBP
            if "€" in salary_str or "eur" in salary_str:
                mid *= 0.86
            elif "cad" in salary_str or ("$" in salary_str and ("ca" in salary_str or "toronto" in location)):
                mid *= 0.58
            elif "$" in salary_str:
                mid *= 0.79
            if mid >= 100_000:
                sal_score = w["salary_match"]
                reasons.append(f"Salary above £100k")
            elif mid >= 80_000:
                sal_score = int(w["salary_match"] * 0.85)
                reasons.append(f"Salary in target range")
            elif mid >= 65_000:
                sal_score = int(w["salary_match"] * 0.5)
            else:
                sal_score = int(w["salary_match"] * 0.2)
        else:
            sal_score = int(w["salary_match"] * 0.8)

    total += sal_score

    # ── 3. Sector / mission match (14 pts) ────────────────────────────────────
    sector_map = {
        "medtech":       ["medtech", "medical technology", "medical device", "medical devices"],
        "healthtech":    ["healthtech", "health tech", "digital health", "health technology"],
        "life sciences": ["life sciences", "life science", "biotech", "biopharma", "pharmaceutical"],
        "deep tech":     ["deep tech", "deeptech", "hard tech", "hardware", "frontier tech", "robotics"],
        "climate":       ["climate", "cleantech", "clean tech", "sustainability", "net zero", "carbon"],
        "agrifood":      ["agrifood", "agri-food", "foodtech", "food tech", "agtech"],
        "saas":          ["saas", "b2b software", "enterprise software"],
    }
    priority_sectors = {"medtech", "healthtech", "life sciences", "deep tech"}
    sector_score = 0
    matched_sector = None
    for sector, variants in sector_map.items():
        if any(v in full for v in variants):
            if sector in priority_sectors:
                sector_score = w["sector_match"]
            else:
                sector_score = int(w["sector_match"] * 0.65)
            matched_sector = sector
            break

    # Startup signal boosts sector score
    if any(s in full for s in ["startup", "start-up", "scale-up", "scaleup", "early-stage", "early stage"]):
        sector_score = min(sector_score + 3, w["sector_match"])

    total += sector_score
    if matched_sector:
        reasons.append(f"Sector: {matched_sector.title()}")

    # ── 4. Founding team quality signals (10 pts) ─────────────────────────────
    team_score = 0
    # Top-tier VC backing
    vc_found = any(vc in full for vc in TOP_TIER_VCS)
    if vc_found:
        team_score = w["founding_team"]
        reasons.append("Top-tier VC backed")
    # Science/technical founders
    sci_found = any(s in full for s in SCIENCE_FOUNDER_SIGNALS)
    if sci_found and not vc_found:
        team_score = int(w["founding_team"] * 0.7)
        reasons.append("Science/technical founders")
    elif sci_found and vc_found:
        team_score = min(team_score + 3, w["founding_team"])

    total += team_score

    # ── 5. Equity / startup stage (6 pts) ─────────────────────────────────────
    stage_score = 0
    stage_map = {
        "series a": 6, "series-a": 6,
        "series b": 5, "series-b": 5,
        "seed": 4, "seed stage": 4, "seed funded": 4,
        "pre-seed": 3, "preseed": 3,
        "series c": 3, "series-c": 3,
    }
    for stage, pts in stage_map.items():
        if stage in full:
            stage_score = min(pts, w["equity_stage"])
            break
    if not stage_score and any(s in full for s in ["startup", "start-up", "venture backed", "vc backed"]):
        stage_score = int(w["equity_stage"] * 0.5)

    total += stage_score
    if stage_score >= 5:
        reasons.append("Series A/B stage")

    # ── 6. Location match (12 pts) ────────────────────────────────────────────
    loc_score = 0
    target_locs = [l.lower() for l in profile["target_locations"]]
    for loc in target_locs:
        if loc in location:
            loc_score = w["location_match"]
            break
    if not loc_score and any(r in location for r in ["remote", "hybrid", "flexible"]):
        loc_score = int(w["location_match"] * 0.5)

    total += loc_score
    if loc_score == w["location_match"]:
        reasons.append(f"Location match")

    # ── 7. Sponsorship likelihood (8 pts) ─────────────────────────────────────
    spon_score = 0
    explicit = job.get("sponsorship_likely")
    if explicit is True:
        spon_score = w["sponsorship_likely"]
    else:
        uk_eu = ["london", "uk", "amsterdam", "netherlands", "paris",
                 "france", "berlin", "germany", "stockholm", "sweden",
                 "copenhagen", "denmark", "edinburgh", "manchester"]
        if any(l in location for l in uk_eu):
            spon_score = int(w["sponsorship_likely"] * 0.75)
        elif any(l in location for l in ["toronto", "canada"]):
            spon_score = int(w["sponsorship_likely"] * 0.6)

    total += spon_score
    if spon_score >= w["sponsorship_likely"] * 0.7:
        reasons.append("Visa sponsorship likely")

    # ── 8. Company size signal (4 pts) ────────────────────────────────────────
    size_score = 0
    small_signals = [
        "15-50", "15 to 50", "20-50", "25-50", "30-50",
        "small team", "small startup", "growing team",
        "series a", "series-a", "seed stage",
        "15 people", "20 people", "25 people", "30 people",
        "40 people", "50 people",
    ]
    large_signals = [
        "500+", "1000+", "10,000", "enterprise", "fortune 500",
        "global company", "multinational", "listed company",
        "public company", "ftse", "nasdaq", "nyse",
    ]
    if any(s in full for s in small_signals):
        size_score = w["company_size"]
    elif not any(l in full for l in large_signals):
        size_score = int(w["company_size"] * 0.5)  # Unknown size, neutral

    total += size_score

    # ── BONUSES ───────────────────────────────────────────────────────────────
    bonus = 0

    # CEO/founder-facing
    if any(s in full for s in ["report to ceo", "reporting to ceo", "report to the ceo",
                                 "work with the ceo", "work closely with ceo",
                                 "founder", "work with founder"]):
        bonus += 5
        bonuses.append("CEO/founder-facing")

    # People leadership explicitly required
    if any(s in full for s in ["manage a team", "managing a team", "people management",
                                 "team leadership", "line management", "direct reports",
                                 "lead a team", "leading a team", "build a team"]):
        bonus += 5
        bonuses.append("People leadership required")

    # External representation
    if any(s in full for s in ["external", "represent", "partnerships", "clients",
                                 "customers", "stakeholders", "conferences"]):
        bonus += 3
        bonuses.append("External-facing role")

    # Commercial track record valued (medium weight)
    if any(s in full for s in ["revenue growth", "revenue target", "sales target",
                                 "commercial track record", "proven commercial",
                                 "grow revenue", "drive revenue", "quota"]):
        bonus += 3
        bonuses.append("Commercial track record valued")

    # Building something (moves away from VC)
    if any(s in full for s in ["build", "scale", "0 to 1", "zero to one",
                                 "greenfield", "from scratch", "early stage"]):
        bonus += 2

    total += bonus

    # ── PENALTIES ─────────────────────────────────────────────────────────────
    penalty = 0

    # Pure VC/investment role
    if any(p in title for p in ["investment analyst", "vc analyst", "venture analyst",
                                  "private equity analyst", "fund manager",
                                  "portfolio analyst"]):
        penalty += 20
        penalties.append("Pure VC/investment role")

    # Large corporate
    if any(p in full for p in ["fortune 500", "ftse 100", "10,000 employees",
                                 "global corporation", "multinational corporation"]):
        penalty += 15
        penalties.append("Large corporate signals")

    # Pure engineering
    if any(p in title for p in ["software engineer", "data scientist", "data engineer",
                                  "machine learning engineer", "devops", "developer",
                                  "programmer", "architect"]):
        penalty += 15
        penalties.append("Technical/engineering role")

    # Consulting/agency
    if any(p in full for p in ["consulting firm", "management consulting",
                                 "agency", "professional services firm",
                                 "advisory firm", "big four", "big 4",
                                 "mckinsey", "bain", "bcg", "deloitte",
                                 "kpmg", "pwc", "ey "]):
        penalty += 10
        penalties.append("Consulting/agency")

    total -= penalty
    total = max(0, min(100, total))

    # ── Build match tags ──────────────────────────────────────────────────────
    match_tags = []
    skill_keywords = [s.lower() for s in profile.get("skills_keywords", [])]
    for kw in skill_keywords:
        if kw in full and len(match_tags) < 4:
            match_tags.append(kw.title())

    # ── Build score reason ────────────────────────────────────────────────────
    all_parts = reasons + [f"+{b}" for b in bonuses]
    if penalties:
        all_parts += [f"⚠ {p}" for p in penalties]
    score_reason = " · ".join(all_parts) if all_parts else "Limited overlap with profile."

    job["score"]        = total
    job["score_reason"] = score_reason
    job["match_tags"]   = match_tags
    return job
