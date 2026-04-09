import os
import time
import threading
import logging

import streamlit as st

# ── Load secrets ──────────────────────────────────────────────────────────────
if "ANTHROPIC_API_KEY" not in os.environ:
    try:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

from src.profile import BRYCE_PROFILE
from src.search_ai import ai_job_search
from src.scraper_linkedin import scrape_linkedin
from src.scraper_indeed import scrape_indeed
from src.scraper_wellfound import scrape_wellfound
from src.scraper_otta import scrape_otta
from src.scraper_glassdoor import scrape_glassdoor
from src.scraper_workinstartups import scrape_workinstartups
from src.company_discovery import discover_company_roles
from src.scorer import score_jobs
from src.doc_generator import generate_cover_letter, generate_cv_summary
from src.storage import load_saved_jobs, save_job, remove_saved_job, update_notes
from src.digest import build_digest

logging.basicConfig(level=logging.WARNING)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bryce Hunt",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .score-high   { background:#d4edda; color:#1a5c30; padding:3px 10px;
                    border-radius:12px; font-size:13px; font-weight:600; }
    .score-mid    { background:#fff3cd; color:#7d5a00; padding:3px 10px;
                    border-radius:12px; font-size:13px; font-weight:600; }
    .score-low    { background:#f8d7da; color:#721c24; padding:3px 10px;
                    border-radius:12px; font-size:13px; font-weight:600; }
    .tag          { background:#e9ecef; color:#495057; padding:2px 8px;
                    border-radius:4px; font-size:12px; margin-right:4px; }
    .match-tag    { background:#d4edda; color:#1a5c30; padding:2px 8px;
                    border-radius:4px; font-size:12px; margin-right:4px; }
    .source-badge { background:#e3f2fd; color:#1565c0; padding:2px 8px;
                    border-radius:4px; font-size:11px; }
    .stage-badge  { background:#f3e5f5; color:#6a1b9a; padding:2px 8px;
                    border-radius:4px; font-size:11px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for _k, _v in [
    ("results", []),
    ("generated_cl", {}),
    ("generated_cv", {}),
    ("last_search_time", None),
    ("search_stats", {}),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Bryce Hunt")
    st.caption("AI-powered job search · v3")
    st.divider()

    st.markdown("### 🔍 Search")

    depth = st.select_slider(
        "AI search depth",
        options=["Quick (8 queries)", "Standard (16 queries)", "Deep (28 queries)"],
        value="Standard (16 queries)",
    )
    depth_map = {"Quick (8 queries)": 8, "Standard (16 queries)": 16, "Deep (28 queries)": 28}
    num_ai = depth_map[depth]

    st.markdown("**Sources**")
    use_ai           = st.checkbox("🤖 AI Web Search",         value=True)
    use_linkedin     = st.checkbox("🔗 LinkedIn",              value=True)
    use_indeed       = st.checkbox("🔎 Indeed",                value=True)
    use_wellfound    = st.checkbox("🚀 Wellfound / AngelList", value=True)
    use_otta         = st.checkbox("⭕ Otta",                  value=True)
    use_glassdoor    = st.checkbox("🔬 Glassdoor",             value=True)
    use_wis          = st.checkbox("💼 WorkInStartups",        value=True)
    use_discovery    = st.checkbox("🏢 Company Discovery",     value=True,
                                   help="Finds Series A/B startups and checks their careers pages directly")

    if use_discovery:
        disc_depth = st.slider("Company discovery queries", 2, 10, 5)
    else:
        disc_depth = 0

    st.divider()
    search_clicked = st.button(
        "🚀 Search All Jobs",
        type="primary",
        use_container_width=True,
    )

    if st.session_state.last_search_time:
        stats = st.session_state.search_stats
        st.caption(f"Last searched: {st.session_state.last_search_time}")
        if stats:
            st.caption(f"Found: {stats.get('total', 0)} roles across {stats.get('sources', 0)} sources")

    st.divider()

    # ── Filters (populated after search) ─────────────────────────────────────
    st.markdown("### 🎚 Filter & Sort")
    min_score = st.slider("Min match score", 0, 100, 35, step=5)

    results_all = st.session_state.results
    all_locs    = sorted({(j.get("location") or "").split(",")[0].strip() for j in results_all if j.get("location")})
    all_srcs    = sorted({j.get("source", "") for j in results_all if j.get("source")})
    all_stages  = sorted({j.get("stage", "") for j in results_all if j.get("stage")})

    filter_locs    = st.multiselect("Location",  all_locs,   placeholder="All locations")
    filter_srcs    = st.multiselect("Source",    all_srcs,   placeholder="All sources")
    filter_stages  = st.multiselect("Stage",     all_stages, placeholder="All stages")
    filter_spon    = st.checkbox("Sponsorship likely only", value=False)

    sort_by = st.selectbox("Sort by", [
        "Match score (best first)",
        "Location",
        "Company (A–Z)",
        "Salary (high first)",
        "Most recent",
    ])

    st.divider()
    with st.expander("Your profile"):
        st.markdown("""
**Bryce Lowen** · NZ Citizen · Relocating now

🎯 CoS · Commercial Lead · COO · Head of Ops · GM  
📍 London · Amsterdam · Paris · Toronto · Scandinavia  
💷 £80k–£110k · 15–50 person startups  
⭐ Series A/B · CEO-facing · People leadership  
✈️ Needs visa sponsorship
        """)


# ── Threaded search runner ────────────────────────────────────────────────────
def _run_search(
    use_ai, num_ai,
    use_linkedin, use_indeed,
    use_wellfound, use_otta,
    use_glassdoor, use_wis,
    use_discovery, disc_depth,
) -> tuple[list[dict], dict]:
    """
    Run all enabled sources in parallel using threads.
    Returns (all_raw_jobs, stats_dict).
    """
    results: dict[str, list] = {}
    errors:  dict[str, str]  = {}
    lock = threading.Lock()

    def run(name, fn, *args):
        try:
            jobs = fn(*args)
            with lock:
                results[name] = jobs
        except Exception as e:
            with lock:
                errors[name] = str(e)
                results[name] = []

    threads = []

    if use_ai:
        t = threading.Thread(target=run, args=("AI Search", ai_job_search, num_ai))
        threads.append(t)

    if use_linkedin:
        for role in ["Chief of Staff", "Head of Operations", "Commercial Lead"]:
            t = threading.Thread(target=run, args=(f"LinkedIn:{role}", scrape_linkedin, role, "London, UK"))
            threads.append(t)

    if use_indeed:
        for role in ["Chief of Staff", "Head of Commercial", "COO"]:
            t = threading.Thread(target=run, args=(f"Indeed:{role}", scrape_indeed, role, "London, UK"))
            threads.append(t)

    if use_wellfound:
        t = threading.Thread(target=run, args=("Wellfound", scrape_wellfound))
        threads.append(t)

    if use_otta:
        t = threading.Thread(target=run, args=("Otta", scrape_otta))
        threads.append(t)

    if use_glassdoor:
        t = threading.Thread(target=run, args=("Glassdoor", scrape_glassdoor))
        threads.append(t)

    if use_wis:
        t = threading.Thread(target=run, args=("WorkInStartups", scrape_workinstartups))
        threads.append(t)

    if use_discovery:
        t = threading.Thread(target=run, args=("CompanyDiscovery", discover_company_roles, disc_depth))
        threads.append(t)

    # Start all threads
    for t in threads:
        t.start()

    # Wait for all to finish
    for t in threads:
        t.join(timeout=300)  # 5 min max per thread

    # Flatten results
    all_jobs = []
    source_counts = {}
    for name, jobs in results.items():
        source_counts[name] = len(jobs)
        all_jobs.extend(jobs)

    stats = {
        "total":   len(all_jobs),
        "sources": len([v for v in source_counts.values() if v > 0]),
        "by_source": source_counts,
        "errors":  errors,
    }
    return all_jobs, stats


# ── Filter & sort ─────────────────────────────────────────────────────────────
def _extract_salary_mid(s):
    if not s:
        return 0
    import re
    nums = re.findall(r"[\d,]+", s)
    nums = [int(n.replace(",", "")) for n in nums if 4 <= len(n.replace(",", "")) <= 7]
    return int(sum(nums) / len(nums)) if nums else 0


def apply_filters(jobs):
    out = [j for j in jobs if j.get("score", 0) >= min_score]
    if filter_locs:
        out = [j for j in out if any(loc.lower() in (j.get("location") or "").lower() for loc in filter_locs)]
    if filter_srcs:
        out = [j for j in out if j.get("source") in filter_srcs]
    if filter_stages:
        out = [j for j in out if j.get("stage") in filter_stages]
    if filter_spon:
        out = [j for j in out if j.get("sponsorship_likely") is True]

    if sort_by == "Match score (best first)":
        out.sort(key=lambda j: j.get("score", 0), reverse=True)
    elif sort_by == "Location":
        out.sort(key=lambda j: (j.get("location") or "").lower())
    elif sort_by == "Company (A–Z)":
        out.sort(key=lambda j: (j.get("company") or "").lower())
    elif sort_by == "Salary (high first)":
        out.sort(key=lambda j: _extract_salary_mid(j.get("salary")), reverse=True)
    elif sort_by == "Most recent":
        out.sort(key=lambda j: j.get("posted_date") or "", reverse=True)
    return out


# ── Job card ──────────────────────────────────────────────────────────────────
def render_card(job: dict, saved_urls: set, tab: str = "results"):
    score = job.get("score", 0)
    badge = (
        f"<span class='score-high'>{score}/100</span>" if score >= 70
        else f"<span class='score-mid'>{score}/100</span>" if score >= 45
        else f"<span class='score-low'>{score}/100</span>"
    )
    stage_html = (
        f"&nbsp;·&nbsp;<span class='stage-badge'>{job['stage']}</span>"
        if job.get("stage") else ""
    )

    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"### {job.get('title', 'Unknown Role')}")
        st.markdown(
            f"**{job.get('company','?')}** &nbsp;·&nbsp; "
            f"📍 {job.get('location','?')} &nbsp;·&nbsp; "
            f"💷 {job.get('salary') or 'Salary not listed'}"
            f"{stage_html} &nbsp;·&nbsp; "
            f"<span class='source-badge'>{job.get('source','?')}</span>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(badge, unsafe_allow_html=True)

    if job.get("score_reason"):
        st.caption(f"💡 {job['score_reason']}")
    if job.get("summary"):
        st.markdown(job["summary"])

    tags_html  = " ".join(f"<span class='tag'>{t}</span>"         for t in job.get("tags", []))
    match_html = " ".join(f"<span class='match-tag'>✓ {t}</span>" for t in job.get("match_tags", []))
    if tags_html or match_html:
        st.markdown(tags_html + " " + match_html, unsafe_allow_html=True)
    st.markdown("")

    job_url = job.get("url") or "#"
    uid = f"{tab}_{abs(hash(job_url))}"
    b1, b2, b3, b4, _ = st.columns([1.2, 1.2, 1.6, 1.6, 3])

    with b1:
        if job_url != "#":
            st.link_button("View ↗", job_url)
    with b2:
        is_saved = job_url in saved_urls
        if st.button("★ Saved" if is_saved else "☆ Save", key=f"save_{uid}"):
            remove_saved_job(job_url) if is_saved else save_job(job)
            st.rerun()
    with b3:
        if st.button("✉ Cover Letter", key=f"cl_{uid}"):
            with st.spinner("Drafting..."):
                st.session_state.generated_cl[job_url] = generate_cover_letter(job, BRYCE_PROFILE)
    with b4:
        if st.button("📄 CV Summary", key=f"cv_{uid}"):
            with st.spinner("Tailoring..."):
                st.session_state.generated_cv[job_url] = generate_cv_summary(job, BRYCE_PROFILE)

    if job_url in st.session_state.generated_cl:
        with st.expander("✉ Cover Letter", expanded=True):
            cl = st.text_area("Edit:", st.session_state.generated_cl[job_url], height=380, key=f"cl_area_{uid}")
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇ Download", cl, file_name=f"CL_{job.get('company','').replace(' ','_')}.txt", key=f"cl_dl_{uid}")
            with c2:
                if st.button("🗑 Clear", key=f"cl_clr_{uid}"):
                    del st.session_state.generated_cl[job_url]; st.rerun()

    if job_url in st.session_state.generated_cv:
        with st.expander("📄 CV Summary", expanded=True):
            cv = st.text_area("Edit:", st.session_state.generated_cv[job_url], height=320, key=f"cv_area_{uid}")
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇ Download", cv, file_name=f"CV_{job.get('company','').replace(' ','_')}.txt", key=f"cv_dl_{uid}")
            with c2:
                if st.button("🗑 Clear", key=f"cv_clr_{uid}"):
                    del st.session_state.generated_cv[job_url]; st.rerun()

    if tab == "saved":
        notes = st.text_area("Notes", value=job.get("notes",""), key=f"notes_{uid}", placeholder="Add notes...", height=80)
        if st.button("💾 Save notes", key=f"savenotes_{uid}"):
            update_notes(job_url, notes); st.success("Saved.")

    st.divider()


# ── Search ────────────────────────────────────────────────────────────────────
if search_clicked:
    st.session_state.results = []
    st.session_state.generated_cl = {}
    st.session_state.generated_cv = {}

    sources_enabled = sum([
        use_ai, use_linkedin, use_indeed,
        use_wellfound, use_otta, use_glassdoor,
        use_wis, use_discovery,
    ])

    with st.status("🔍 Searching across all sources in parallel...", expanded=True) as status:
        st.write(f"Running {sources_enabled} sources simultaneously. This will take 3–8 minutes...")
        st.write("☕ Good time for a coffee.")

        start_time = time.time()
        raw, stats = _run_search(
            use_ai, num_ai,
            use_linkedin, use_indeed,
            use_wellfound, use_otta,
            use_glassdoor, use_wis,
            use_discovery, disc_depth,
        )
        elapsed = int(time.time() - start_time)

        st.write(f"⚡ Scoring and ranking {len(raw)} listings...")
        scored = score_jobs(raw, BRYCE_PROFILE)
        st.session_state.results = scored
        st.session_state.last_search_time = time.strftime("%d %b %Y, %H:%M")
        st.session_state.search_stats = {**stats, "total": len(scored)}

        # Show per-source breakdown
        st.write("**Results by source:**")
        for src, count in sorted(stats["by_source"].items(), key=lambda x: -x[1]):
            icon = "✅" if count > 0 else "⚠️"
            st.write(f"  {icon} {src}: {count} listings")
        if stats.get("errors"):
            for src, err in stats["errors"].items():
                st.write(f"  ❌ {src} error: {err[:80]}")

        status.update(
            label=f"✅ Done in {elapsed}s — {len(scored)} roles found across {stats['sources']} sources",
            state="complete",
            expanded=False,
        )

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_results, tab_saved, tab_digest = st.tabs(["🔍 Results", "⭐ Saved", "📋 Digest"])

with tab_results:
    results = st.session_state.results
    if not results:
        st.info("👈 Hit **Search All Jobs** in the sidebar. Searches 8 sources and 20+ queries simultaneously — grab a coffee while it runs.")
    else:
        filtered = apply_filters(results)
        high  = sum(1 for j in filtered if j.get("score", 0) >= 70)
        mid   = sum(1 for j in filtered if 45 <= j.get("score", 0) < 70)
        locs  = len({(j.get("location") or "").split(",")[0] for j in filtered})
        srcs  = len({j.get("source") for j in filtered if j.get("source")})

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Showing",       len(filtered))
        c2.metric("Total found",   len(results))
        c3.metric("Strong (70+)",  high)
        c4.metric("Solid (45–69)", mid)
        c5.metric("Sources",       srcs)

        if len(filtered) < len(results):
            st.caption(f"Filtered from {len(results)} → {len(filtered)}. Adjust sidebar filters to see more.")
        st.divider()

        if not filtered:
            st.warning("No results match current filters. Try lowering the minimum score.")
        else:
            saved_urls = {j.get("url") for j in load_saved_jobs()}
            for job in filtered:
                render_card(job, saved_urls, tab="results")

with tab_saved:
    saved = load_saved_jobs()
    if not saved:
        st.info("No saved roles yet — hit ☆ Save on any result.")
    else:
        saved_urls = {j.get("url") for j in saved}
        st.markdown(f"**{len(saved)} saved roles**")
        for job in saved:
            render_card(job, saved_urls, tab="saved")

with tab_digest:
    saved   = load_saved_jobs()
    results = st.session_state.results
    choice  = st.radio("Digest from:", ["Saved jobs", "All results"], horizontal=True)
    pool    = saved if choice == "Saved jobs" else results
    if not pool:
        st.info("Run a search or save some roles first.")
    else:
        digest = build_digest(pool)
        st.text_area("Email-ready digest:", digest, height=440)
        st.download_button("⬇ Download (.txt)", digest, file_name="bryce_job_digest.txt")
