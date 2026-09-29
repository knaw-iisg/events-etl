"""Crawling iisg.amsterdam's events pages: the current-events listing, the
paginated archive listing, and individual event detail pages."""

from __future__ import annotations

import time
from collections.abc import Iterator

import requests
from bs4 import BeautifulSoup

from .prefixes import SITE_BASE

CURRENT_URL = f"{SITE_BASE}/en/events"
ARCHIVE_URL = f"{SITE_BASE}/en/events/archive"

USER_AGENT = "events-etl/0.1 (+https://github.com/knaw-iisg/events-etl)"

_MAX_RETRIES = 5
_RETRY_BACKOFF_SECONDS = 3


def _get_with_retry(http: requests.Session, url: str, *, params: dict | None, timeout: float) -> requests.Response:
    """Transient connection drops are expected over a ~170-page crawl, not
    exceptional -- same reasoning as the sibling repos' OAI-PMH harvesters."""
    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = http.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
    raise last_error


def _absolute(url: str) -> str:
    return url if url.startswith("http") else SITE_BASE + url


def _listing_entries(html: str) -> list[dict]:
    """Each teaser on a listing page carries both the event's detail-page
    URL and a pre-cropped thumbnail image URL (Drupal image style
    ``12x7_524w``) that never appears on the detail page itself -- the
    detail page only has the uncropped original. Harvested here, once,
    while discovering the URL, rather than guessed later."""
    soup = BeautifulSoup(html, "lxml")
    entries = []
    for node in soup.select("div.node--type-event"):
        link = node.select_one("a.full-click__trigger[href]")
        if link is None:
            continue
        img = node.select_one(".field--name-teaser-image img[src]")
        entries.append({
            "url": _absolute(link["href"]),
            "thumbnail_url": _absolute(img["src"]) if img is not None else None,
        })
    return entries


def iter_event_listing_entries(
    *, session: requests.Session | None = None, timeout: float = 30, delay: float = 0.5,
) -> Iterator[dict]:
    """Yield one ``{"url": ..., "thumbnail_url": ...}`` dict per event,
    deduplicated by URL, from the current listing plus every page of the
    archive listing. ``delay`` is a polite pause between requests to a site
    with no published rate-limit policy."""
    http = session or requests.Session()
    http.headers["User-Agent"] = USER_AGENT

    seen: set[str] = set()

    def emit(entries: list[dict]) -> Iterator[dict]:
        for entry in entries:
            if entry["url"] not in seen:
                seen.add(entry["url"])
                yield entry

    resp = _get_with_retry(http, CURRENT_URL, params=None, timeout=timeout)
    yield from emit(_listing_entries(resp.text))

    page = 0
    while True:
        resp = _get_with_retry(http, ARCHIVE_URL, params={"page": page}, timeout=timeout)
        entries = _listing_entries(resp.text)
        if not entries:
            return
        yield from emit(entries)
        page += 1
        time.sleep(delay)


def fetch_event_html(url: str, *, session: requests.Session | None = None, timeout: float = 30) -> str:
    http = session or requests.Session()
    http.headers.setdefault("User-Agent", USER_AGENT)
    resp = _get_with_retry(http, url, params=None, timeout=timeout)
    return resp.text
