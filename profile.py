"""
Bryce Lowen — candidate profile.
All scoring weights and preferences derived from interview responses.
"""

BRYCE_PROFILE = {
    "name": "Bryce Lowen",
    "email": "brycelowen@gmail.com",
    "phone": "+64 21 343 230",
    "linkedin": "www.linkedin.com/in/brycelowen",
    "citizenship": "New Zealand",
    "needs_visa_sponsorship": True,

    # ── Target roles ──────────────────────────────────────────────────────────
    "target_roles": [
        "Chief of Staff",
        "Commercial Lead",
        "Head of Commercial",
        "COO",
        "Chief Operating Officer",
        "Head of Operations",
        "Operations Manager",
        "Business Development Lead",
        "VP of Operations",
        "General Manager",
        "Head of BD",
        "Head of Partnerships",
        "Investor Relations",        # VC background welcomed here
        "Head of Growth",
        "Country Manager",
    ],

    # ── Ideal week (from Q1) ──────────────────────────────────────────────────
    # Leading commercial/sales, managing a team, external representation,
    # working directly with CEO/founder
    "ideal_week": [
        "leading commercial or sales function",
        "managing a team",
        "representing company externally",
        "working directly with ceo",
        "working directly with founder",
    ],

    # ── Moving AWAY from (from Q2) ────────────────────────────────────────────
    # Too removed from building, not enough people leadership,
    # slow pace, wanted more ownership
    "moving_away_from": [
        "pure investment analysis",
        "financial modelling",
        "slow pace",
        "no ownership",
        "no people leadership",
    ],

    # ── Locations ─────────────────────────────────────────────────────────────
    "target_locations": [
        "London", "UK", "United Kingdom",
        "Amsterdam", "Netherlands",
        "Paris", "France",
        "Toronto", "Canada",
        "Stockholm", "Sweden",
        "Copenhagen", "Denmark",
        "Berlin", "Germany",
        "Edinburgh", "Manchester",
    ],

    # ── Sectors (preferred, not exclusive) ────────────────────────────────────
    "target_sectors": [
        "MedTech", "HealthTech", "Life Sciences", "Biotech",
        "Deep Tech", "Hard Tech", "Medical Device", "Digital Health",
        "AgriFood", "FoodTech", "Climate", "CleanTech",
    ],

    # ── Company preferences (from Q6) ─────────────────────────────────────────
    "preferred_company_types": [
        "top-tier vc backed",      # Sequoia, a16z, Index, Atomico etc.
        "science founded",         # scientists or technical founders
    ],

    # ── Company size (from Q3): Small — 15 to 50 people ──────────────────────
    "preferred_size_min": 15,
    "preferred_size_max": 50,

    # ── Salary ────────────────────────────────────────────────────────────────
    "target_salary_min_gbp": 80_000,
    "target_salary_max_gbp": 110_000,
    # Roles without salary: assume in range (score normally)
    "no_salary_penalty": 0,

    # ── Experience level (from Q8): 5–8 years ─────────────────────────────────
    "experience_years_min": 5,
    "experience_years_max": 8,

    # ── VC roles: include (from Q5) ───────────────────────────────────────────
    "include_vc_adjacent": True,
    "vc_adjacent_penalty": 0,

    # ── Stage ─────────────────────────────────────────────────────────────────
    "target_stage": ["Seed", "Series A", "Series B", "Pre-seed"],

    # ── Priority ranking (from Q4, ranked 1–5) ────────────────────────────────
    # 1. Role title and seniority
    # 2. High salary (£100k+)
    # 3. Company mission and sector
    # 4. Quality of the founding team
    # 5. Equity / ownership upside
    "priority_ranking": [
        "role_title_seniority",
        "salary",
        "mission_sector",
        "founding_team_quality",
        "equity",
    ],

    # ── Scoring weights (calibrated to priority ranking above) ────────────────
    # Total = 100 points
    "scoring_weights": {
        "role_match":           28,   # #1 priority — role title & seniority
        "salary_match":         18,   # #2 priority — salary
        "sector_match":         14,   # #3 priority — mission & sector
        "founding_team":        10,   # #4 priority — team quality signals
        "equity_stage":          6,   # #5 priority — equity/startup stage
        "location_match":       12,   # practical necessity
        "sponsorship_likely":    8,   # practical necessity
        "company_size":          4,   # 15–50 people preference
    },

    # ── Commercial weighting: medium (from Q7) ────────────────────────────────
    # Used as a bonus signal, not primary driver
    "commercial_weight": "medium",

    # ── Mission importance: important but secondary (from Q3) ─────────────────
    "mission_importance": "secondary",

    # ── Skills keywords for matching ──────────────────────────────────────────
    "skills_keywords": [
        # Role signals
        "chief of staff", "commercial lead", "head of commercial",
        "coo", "head of operations", "operations manager",
        "general manager", "country manager", "head of growth",
        "business development", "bd", "partnerships",
        "investor relations", "fundraising",
        # What he wants to DO
        "people leadership", "team management", "managing a team",
        "external representation", "ceo", "founder",
        "revenue growth", "go-to-market", "gtm", "commercial strategy",
        "scale", "build", "ownership",
        # His background signals
        "medtech", "medical device", "healthtech", "life sciences",
        "regulatory", "market access", "clinical",
        "venture capital", "vc", "portfolio", "due diligence",
        "startup", "scale-up", "series a", "series b", "seed",
        # Company quality signals
        "sequoia", "a16z", "andreessen", "index ventures", "atomico",
        "accel", "benchmark", "general catalyst", "bessemer",
        "lightspeed", "tiger global", "softbank",
    ],

    # ── Background summary for AI prompts ────────────────────────────────────
    "background_summary": """
Bryce Lowen — NZ citizen, relocating immediately to UK/Europe/Canada. Needs visa sponsorship.

WHAT HE WANTS:
- Role: Chief of Staff, Commercial Lead, COO, Head of Operations, GM, BD Lead
- Ideal week: Leading commercial/sales function, managing a team, representing company 
  externally, working directly with CEO/founder daily
- Moving away from: pure VC (too removed from building, no people leadership, slow pace)
- Company size: 15–50 people (small startup, post-seed to Series B)
- Prefers: top-tier VC-backed, science/technical founders
- Salary: £80k–£110k. Role title/seniority is #1 priority.
- Open to VC-adjacent roles at startups (investor relations, fundraising)

EXPERIENCE (~6 years total, sweet spot 5–8 year roles):
- NZ Growth Capital Partners: Senior Investment Analyst / Portfolio Manager (2023–present)
  Full investment cycle, board observer (MACSO, ProTag), due diligence, deal execution
- Fisher & Paykel Healthcare: Product Specialist RAC (2021–2023)
  Grew territory revenue 59% in 12 months, capital equipment +39%, consumables +57%
  Clinical advisor, nurse education, product launches
- Fisher & Paykel Healthcare: Regulatory Affairs Associate (2019–2021)
  Product registrations, ISO 13485, multi-market regulatory submissions
- Synergus AB, Stockholm: Research Analyst Intern (2017)
  IVD market access, reimbursement mechanisms, European healthcare systems
- IDNZ: Cruise Operations Coordinator (2018–2019)

EDUCATION:
- Master of Bioscience Enterprise, First Class Honours — Auckland & Karolinska Institute (2017)
- BSc Biomedical Science — University of Auckland

KEY STRENGTHS:
- Commercial results with hard numbers (59% revenue growth)
- VC deal execution and portfolio management
- Medical device / MedTech / regulatory background
- European networks (Stockholm, Karolinska)
- Stakeholder engagement across clinical, investor, and founder audiences
- Moving toward: people leadership, building things, ownership, fast pace
""",

    # ── Full CV for document generation ───────────────────────────────────────
    "cv_text": """
BRYCE LOWEN
brycelowen@gmail.com | +64 21 343 230 | linkedin.com/in/brycelowen

EXPERIENCE

NZ Growth Capital Partners — Auckland, NZ
Senior Investment Analyst (Aug 2024–present) / Portfolio Manager (May 2023–Aug 2024)
• Full investment cycle: origination, screening, due diligence, execution, board observer
• Board observer at MACSO and ProTag; strategic insight and growth guidance
• Directed follow-on capital allocation and divestment initiatives
• Built relationships across portfolio companies, investors, and ecosystem stakeholders

Fisher & Paykel Healthcare — Auckland, NZ
Product Specialist – Respiratory & Acute Care (Jul 2021–May 2023)
• Grew territory revenue 59% in first 12 months; capital equipment +39%, consumables +57%
• Launched new medical devices; contributed to R&D product development feedback
• Clinical advisor to hospital staff; delivered nurse education and clinical presentations

Regulatory Affairs Associate (Sep 2019–Jul 2021)
• Managed product registrations and regulatory submissions across multiple markets
• ISO 13485 QMS compliance; supported audit preparation
• Regulatory advice throughout product development lifecycle

Synergus AB — Stockholm, Sweden
Research Analyst Intern (Jun–Dec 2017)
• Analysed IVD medical device introduction into European healthcare systems
• Investigated reimbursement mechanisms for point-of-care diagnostics
• Research formed basis of Master's thesis

IDNZ — Auckland, NZ
Cruise Operations Coordinator (Aug 2018–May 2019)
• End-to-end shore excursion operations: itinerary, reservations, delivery, invoicing

EDUCATION
Master of Bioscience Enterprise, First Class Honours
University of Auckland & Karolinska Institute, Stockholm — 2017

BSc Biomedical Science — University of Auckland — 2012–2015

ACHIEVEMENTS
• Karolinska Institute Exchange Scholarship, 2017
• Top of class — Scient 706 Commercialisation Research Project, 2016
""",
}
