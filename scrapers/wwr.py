"""
We Work Remotely scraper — uses public RSS feeds, no auth, ToS-compliant.
Fetches from multiple tech category feeds and optionally filters by keyword.
"""

import html
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import quote_plus

import feedparser

_CATEGORY_FEEDS = {
    "programming": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "devops": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "data": "https://weworkremotely.com/categories/remote-data-science-jobs.rss",
}

_HEADERS = {
    "User-Agent": "job-radar/1.0 (personal job search agent; RSS reader)",
    "Accept": "application/rss+xml, application/xml, */*",
}


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_title_and_company(raw: str) -> tuple[str, str]:
    """WWR titles are 'Company: Job Title'. Split on the first ': '."""
    if ": " in raw:
        company, title = raw.split(": ", 1)
        return title.strip(), company.strip()
    return raw.strip(), "Unknown"


def _parse_date(entry) -> Optional[datetime]:
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        return None


def _fetch_feed(url: str) -> list[dict]:
    feed = feedparser.parse(url, request_headers=_HEADERS)
    jobs: list[dict] = []
    for entry in feed.entries:
        raw_title = entry.get("title", "").strip()
        if not raw_title:
            continue

        job_title, company = _parse_title_and_company(raw_title)
        description = _strip_html(entry.get("summary") or entry.get("description") or "")
        url_val = entry.get("link", "")

        jobs.append(
            {
                "title": job_title,
                "company": company,
                "location": "Remote",
                "description": description,
                "url": url_val,
                "source": "wwr",
                "date_posted": _parse_date(entry),
            }
        )
    return jobs


def fetch_jobs(
    query: str = "",
    categories: list[str] | None = None,
    limit: int = 50,
) -> list[dict]:
    """Fetch remote tech jobs from We Work Remotely.

    Args:
        query: Optional keyword filter. If provided, also fetches the
               WWR keyword search feed in addition to category feeds.
        categories: Which category feeds to fetch from. Defaults to
                    programming + devops + data.
        limit: Max jobs to return after filtering.
    """
    cats = categories or list(_CATEGORY_FEEDS.keys())

    all_jobs: list[dict] = []
    seen_urls: set[str] = set()

    # Fetch category feeds
    for cat in cats:
        feed_url = _CATEGORY_FEEDS.get(cat)
        if not feed_url:
            print(f"[wwr] Unknown category '{cat}', skipping")
            continue
        for job in _fetch_feed(feed_url):
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                all_jobs.append(job)

    # Also fetch the keyword search feed if a query is given
    if query:
        search_url = f"https://weworkremotely.com/remote-jobs/search.rss?term={quote_plus(query)}"
        for job in _fetch_feed(search_url):
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                all_jobs.append(job)

    # Client-side keyword filter: ALL words must appear in title OR description
    if query:
        words = query.lower().split()
        all_jobs = [
            j for j in all_jobs
            if all(
                w in j["title"].lower() or w in j["description"].lower()
                for w in words
            )
        ]

    return all_jobs[:limit]
