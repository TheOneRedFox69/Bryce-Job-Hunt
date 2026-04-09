"""
Build a plain-text email digest from a list of job results.
"""

from datetime import datetime


def build_digest(jobs: list[dict]) -> str:
    date_str = datetime.now().strftime("%d %B %Y")
    lines = [
        "═══════════════════════════════════════════════════",
        "  BRYCE LOWEN — JOB SEARCH DIGEST",
        f"  Generated: {date_str}",
        "═══════════════════════════════════════════════════",
        "",
    ]

    high   = [j for j in jobs if j.get("score", 0) >= 70]
    medium = [j for j in jobs if 45 <= j.get("score", 0) < 70]
    low    = [j for j in jobs if j.get("score", 0) < 45]

    def fmt_section(title: str, section_jobs: list[dict]) -> list[str]:
        if not section_jobs:
            return []
        out = [f"── {title} ({len(section_jobs)} roles) ──────────────────────────", ""]
        for i, j in enumerate(section_jobs, 1):
            out += [
                f"  {i}. {j.get('title', '?')}",
                f"     Company:   {j.get('company', '?')}",
                f"     Location:  {j.get('location', '?')}",
                f"     Salary:    {j.get('salary') or 'Not listed'}",
                f"     Score:     {j.get('score', 0)}/100",
                f"     Source:    {j.get('source', '?')}",
                f"     URL:       {j.get('url', '?')}",
                f"     Notes:     {j.get('notes') or '—'}",
                f"     Why:       {j.get('score_reason') or '—'}",
                "",
            ]
        return out

    lines += fmt_section("★ STRONG MATCHES (70+)", high)
    lines += fmt_section("◐ SOLID MATCHES (45–69)", medium)
    lines += fmt_section("○ LOWER MATCHES (<45)", low)

    lines += [
        "═══════════════════════════════════════════════════",
        f"  Total: {len(jobs)} roles | Strong: {len(high)} | Solid: {len(medium)} | Low: {len(low)}",
        "═══════════════════════════════════════════════════",
    ]

    return "\n".join(lines)
