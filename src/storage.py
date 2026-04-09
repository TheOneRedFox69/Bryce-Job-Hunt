"""
Simple JSON file storage for saved jobs and notes.
In Streamlit Cloud, writes to /tmp (ephemeral). For persistence,
swap this module out for a Supabase / SQLite / st.session_state based store.
"""

import json
import os
from pathlib import Path

_STORAGE_FILE = Path(os.environ.get("JOBS_STORAGE_PATH", "/tmp/bryce_saved_jobs.json"))


def _load() -> list[dict]:
    if not _STORAGE_FILE.exists():
        return []
    try:
        return json.loads(_STORAGE_FILE.read_text())
    except Exception:
        return []


def _save(jobs: list[dict]) -> None:
    _STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STORAGE_FILE.write_text(json.dumps(jobs, indent=2))


def load_saved_jobs() -> list[dict]:
    return _load()


def save_job(job: dict) -> None:
    jobs = _load()
    url = job.get("url", "")
    # Avoid duplicates
    if not any(j.get("url") == url for j in jobs):
        jobs.append(job)
        _save(jobs)


def remove_saved_job(url: str) -> None:
    jobs = _load()
    jobs = [j for j in jobs if j.get("url") != url]
    _save(jobs)


def update_notes(url: str, notes: str) -> None:
    jobs = _load()
    for job in jobs:
        if job.get("url") == url:
            job["notes"] = notes
            break
    _save(jobs)
