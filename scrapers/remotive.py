"""
Remotive scraper — uses Remotive's public JSON API.
No authentication, no rate-limit concerns for personal use.
API docs: https://remotive.com/api/remote-jobs
"""

from datetime import datetime
from typing import Optional

import requests

_API_URL = "https://remotive.com/api/remote-jobs"

# Remotive category slugs that match software/tech roles
_CATEGORIES = [
    "software-dev",
    "devops-sysadmin",
    "data",
]

_HEADERS = {
    "User-Agent": "job-radar/1.0 (personal job search agent)",
    "Accept": "application/json",
}


def _parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str[:19], fmt)
        except ValueError:
            continue
    return None


def _strip_html(text: str) -> str:
    import html
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_jobs(
    query: str = "",
    categories: list[str] | None = None,
    limit: int = 50,
) -> list[dict]:
    """Fetch remote job listings from Remotive's public API.

    Args:
        query: Optional keyword filter (applied client-side on title + description).
        categories: Remotive category slugs to fetch from. Defaults to software/data/devops.
        limit: Max number of jobs to return after filtering.

    Returns a list of dicts compatible with db.models.Job.
    """
    cats = categories or _CATEGORIES
    raw: list[dict] = []

    for cat in cats:
        try:
            resp = requests.get(
                _API_URL,
                params={"category": cat},
                headers=_HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            raw.extend(resp.json().get("jobs", []))
        except requests.RequestException as exc:
            print(f"[remotive] Failed to fetch category '{cat}': {exc}")
            continue

    # Deduplicate by job id within this batch
    seen_ids: set[int] = set()
    unique: list[dict] = []
    for job in raw:
        if job["id"] not in seen_ids:
            seen_ids.add(job["id"])
            unique.append(job)

    # Keyword filter: ALL words must appear in title OR description
    if query:
        words = query.lower().split()
        unique = [
            j for j in unique
            if all(
                w in j.get("title", "").lower() or w in j.get("description", "").lower()
                for w in words
            )
        ]

    jobs: list[dict] = []
    for j in unique[:limit]:
        jobs.append(
            {
                "title": j.get("title", "").strip(),
                "company": j.get("company_name", "Unknown").strip(),
                "location": j.get("candidate_required_location") or "Remote",
                "description": _strip_html(j.get("description", "")),
                "url": j.get("url", ""),
                "source": "remotive",
                "date_posted": _parse_date(j.get("publication_date", "")),
            }
        )

    return jobs
