"""
Indeed RSS scraper — ToS-compliant, read-only, no authentication required.

Indeed publishes public RSS feeds for any job search. Rate limit: keep
requests infrequent (a few per day) and use the `fromage` param to fetch
only recent listings so you're not hammering the same data repeatedly.
"""

import html
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse

import feedparser

_RSS_BASE = "https://www.indeed.com/rss"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def build_rss_url(query: str, location: str = "remote", days_old: int = 3) -> str:
    params = {"q": query, "l": location, "sort": "date", "fromage": days_old}
    return f"{_RSS_BASE}?{urlencode(params)}"


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_url(url: str) -> str:
    """Return a stable canonical URL using Indeed's job key (jk param).
    This prevents the same listing from being stored twice with different
    tracking parameters appended by RSS."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    jk = params.get("jk", [None])[0]
    if jk:
        return f"https://www.indeed.com/viewjob?jk={jk}"
    return url


def _parse_title_and_company(raw_title: str) -> tuple[str, Optional[str]]:
    """Indeed titles are often 'Job Title - Company Name'.
    Split on the last ' - ' so multi-word titles like 'Sr. SWE - Backend - Stripe'
    yield title='Sr. SWE - Backend', company='Stripe'."""
    parts = raw_title.rsplit(" - ", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return raw_title.strip(), None


def _parse_date(entry) -> Optional[datetime]:
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        return None


def fetch_jobs(
    query: str,
    location: str = "remote",
    days_old: int = 3,
) -> list[dict]:
    """Fetch job listings from the Indeed RSS feed.

    Returns a list of dicts ready to be stored as db.models.Job rows.
    Guarantees every entry has: title, company, location, description,
    url, source, date_posted.
    """
    url = build_rss_url(query, location, days_old)
    feed = feedparser.parse(url, request_headers=_HEADERS)

    if not feed.entries:
        # Indeed actively blocks automated RSS access (returns 403 Security Check).
        # To use Indeed reliably, integrate via Apify's Indeed actor which runs a
        # real browser session. See: https://apify.com/misceres/indeed-scraper
        print(
            "\n[indeed] WARNING: No jobs returned — Indeed blocked the request (403).\n"
            "  Option 1: Set up Apify integration (recommended, ~$5-15/month).\n"
            "  Option 2: Use 'python main.py fetch --source remotive' as a free alternative.\n"
        )
        return []

    jobs: list[dict] = []
    for entry in feed.entries:
        raw_title = entry.get("title", "").strip()
        if not raw_title:
            continue

        job_title, company = _parse_title_and_company(raw_title)

        # Fall back to author field if title had no company segment
        if not company:
            company = entry.get("author", "").strip() or "Unknown"

        summary_html = entry.get("summary") or entry.get("description") or ""
        description = _strip_html(summary_html)

        raw_url = entry.get("link", "")
        canonical_url = _normalize_url(raw_url) if raw_url else ""

        jobs.append(
            {
                "title": job_title,
                "company": company,
                "location": location,
                "description": description,
                "url": canonical_url,
                "source": "indeed",
                "date_posted": _parse_date(entry),
            }
        )

    return jobs
