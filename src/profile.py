"""
Bryce Lowen's candidate profile.
Edit this file to update scoring criteria and document generation context.
"""

BRYCE_PROFILE = {
    "name": "Bryce Lowen",
    "email": "brycelowen@gmail.com",
    "phone": "+64 21 343 230",
    "linkedin": "www.linkedin.com/in/brycelowen",
    "citizenship": "New Zealand",
    "needs_visa_sponsorship": True,

    # ── Target preferences ────────────────────────────────────────────────────
    "target_roles": [
        "Chief of Staff",
        "Commercial Lead",
        "COO",
        "Head of Operations",
        "Operations Manager",
        "Business Development Lead",
        "General Manager",
    ],
    "target_locations": [
        "London", "UK", "Amsterdam", "Netherlands",
        "Paris", "France", "Toronto", "Canada",
        "Stockholm", "Copenhagen", "Berlin", "Scandinavia",
    ],
    "target_sectors": [
        "MedTech", "HealthTech", "Life Sciences", "Biotech",
        "Deep Tech", "Hard Tech", "Medical Device",
    ],
    "target_salary_min_gbp": 80_000,
    "target_salary_max_gbp": 110_000,
    "target_stage": ["Pre-seed", "Seed", "Series A", "Series B"],
    "work_style": "in-office",
    "wants_equity": True,

    # ── What to prioritise in scoring ────────────────────────────────────────
    "scoring_weights": {
        "role_match": 30,        # title / role type match
        "sector_match": 20,      # industry alignment
        "location_match": 15,    # geography
        "stage_match": 10,       # startup stage
        "salary_match": 10,      # salary range fit
        "sponsorship_likely": 10, # UK/EU companies more likely to sponsor
        "skills_match": 5,       # specific skill keywords
    },

    # ── Skills & keywords to match against job descriptions ──────────────────
    "skills_keywords": [
        "commercial", "operations", "chief of staff", "go-to-market",
        "strategy", "stakeholder", "fundraising", "investor relations",
        "due diligence", "portfolio", "board", "revenue", "growth",
        "medical device", "medtech", "healthtech", "life sciences",
        "regulatory", "market access", "clinical", "venture capital",
        "startup", "scale-up", "series a", "series b",
        "business development", "partnerships", "sales",
    ],

    # ── Experience summary for AI prompts ────────────────────────────────────
    "background_summary": """
Bryce Lowen is a New Zealand citizen based in Auckland, actively seeking to relocate 
immediately to the UK, Europe, or Canada. He holds NZ citizenship and will require 
visa sponsorship.

CURRENT ROLE: Senior Investment Analyst at NZ Growth Capital Partners (Aug 2024–present)
- Full investment cycle: origination, screening, due diligence, execution, portfolio support
- Board observer at MACSO and ProTag (both early-stage portfolio companies)
- Previously Portfolio Manager (May 2023–Aug 2024): follow-on investments, divestments

PRIOR: Fisher & Paykel Healthcare (Sep 2019–May 2023, ~4 years)
- Product Specialist, Respiratory & Acute Care: grew territory revenue 59% in 12 months,
  capital equipment +39%, consumables +57% over two years; clinical advisor
- Regulatory Affairs Associate: product registrations, regulatory submissions, ISO 13485 QMS

EARLIER: 
- Cruise Operations Coordinator, IDNZ (Aug 2018–May 2019)
- Research Analyst Intern, Synergus AB, Stockholm (Jun–Dec 2017): IVD market access,
  reimbursement mechanisms for point-of-care diagnostics in European healthcare systems
- Senior Advisor, Rotary NSTF (Summers 2012–2015)

EDUCATION:
- Master of Bioscience Enterprise, First Class Honours — Univ. of Auckland & Karolinska 
  Institute, Stockholm (2017). Research focused on introduction of IVD devices into European 
  healthcare systems; thesis on reimbursement mechanisms for point-of-care diagnostics.
- PG Diploma Bioscience Enterprise with Merit — Univ. of Auckland (2016)
- BSc Biomedical Science — Univ. of Auckland (2012–2015)

ACHIEVEMENTS:
- Karolinska Institute Exchange Scholarship, 2017
- Top of class in Scient 706 – Commercialisation Research Project, 2016

LANGUAGES: English (native), Swedish (some)

STRENGTHS:
- VC deal execution, due diligence, financial modelling
- Medical device sales with strong commercial results
- Regulatory affairs and market access
- Stakeholder engagement (founders, investors, clinical staff)
- Strategic planning, portfolio support, board-level communication
- European networks (Stockholm, Karolinska ecosystem)

IDEAL ROLE: 
Wants to move from pure VC into a startup operating role. Excited to be closer to 
building companies rather than investing in them. Best fit: Chief of Staff, Commercial 
Lead, COO, or Operations Manager at a Series A/B startup (open to seed). Wants to 
build and scale — commercial growth, operational foundations. Happy in-office.
""",

    # ── Full CV text for document generation ────────────────────────────────
    "cv_text": """
BRYCE LOWEN
brycelowen@gmail.com | +64 21 343 230 | www.linkedin.com/in/brycelowen

EXPERIENCE

NZ Growth Capital Partners — Auckland, NZ
Senior Investment Analyst (Aug 2024–present) / Portfolio Manager (May 2023–Aug 2024)
• Proactively identifies and evaluates investment opportunities through market research, 
  networking, and engagement within the startup and investor ecosystem
• Leads full investment cycle: origination, screening, due diligence, execution, board obs.
• Board observer at MACSO and ProTag; provides strategic insight and growth guidance
• Directs follow-on capital allocation; leads divestment initiatives
• Cultivates relationships with portfolio companies, investors, and ecosystem stakeholders

Fisher & Paykel Healthcare — Auckland, NZ
Product Specialist – Respiratory and Acute Care (Jul 2021–May 2023)
• Grew territory revenue 59% in first 12 months; capital equipment +39%, consumables +57%
• Launched new medical devices; contributed to R&D and product development feedback
• Positioned as trusted clinical advisor; delivered nurse education and clinical presentations
• Identified customer needs, provided customised solutions driving clinical change

Regulatory Affairs Associate (Sep 2019–Jul 2021)
• Managed product registrations and regulatory submissions across multiple markets
• Provided regulatory advice throughout product development lifecycle
• Supported QMS audits; ensured ISO 13485 compliance
• Built cross-functional relationships to ensure efficient information flow

Synergus AB — Stockholm, Sweden
Research Analyst Intern (Jun 2017–Dec 2017)
• Analysed factors influencing introduction of IVD medical devices in Europe
• Investigated reimbursement mechanisms for point-of-care diagnostics in European systems
• Identified key stakeholders in reimbursement process
• Research formed basis of Master's thesis

IDNZ — Auckland, NZ
Cruise Operations Coordinator (Aug 2018–May 2019)
• Coordinated shore excursion operations end-to-end: itinerary, reservations, guest comms,
  on-ground delivery, invoicing
• Maintained relationships with ship staff, cruise line HQs, and local operators

Rotary National Science and Technology Forum — Auckland, NZ
Senior Advisor (Summers 2012–2015)
• Supervised 30 students aged 17–18 during two-week residential programme, four summers
• Coordinated daily schedules for academic, industry, and recreational activities
• Primary contact for student welfare, health, and behavioural matters

EDUCATION
Master of Bioscience Enterprise, First Class Honours
University of Auckland & Karolinska Institute, Stockholm — 2017

Postgraduate Diploma of Bioscience Enterprise with Merit
University of Auckland — 2016

Bachelor of Science in Biomedical Science
University of Auckland — 2012–2015

ACHIEVEMENTS
• Karolinska Institute Exchange Scholarship recipient, 2017
• Top of class — Scient 706, Commercialisation Research Project, 2016
• Senior Advisor — Rotary National Science and Technology Forum, 2014–2015
""",
}
