"""Extracting a structured record from one event detail page's HTML.

The page's "Practical information" block (``Venue``/``Place``/``Location``,
``Language``, ...) is free text with no consistent field markup -- confirmed
across a sample of real pages, where the same fact appears under different
labels ("Venue" vs "Place" vs "Location") or is missing outright. Facts are
mined from it on a best-effort basis; nothing is guessed when a label isn't
found.
"""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

# (day month year, hour:minute) pairs, in either order of separator the site
# uses: a plain space (listing teasers, e.g. "6 October 2026 16:00") or a
# hyphen (detail pages, e.g. "06 October 2026 - 16:00"). A range is two such
# pairs, joined by an em dash on detail pages or a hyphen on teasers -- that
# joiner is deliberately not matched here, since it's never part of either
# date-time pair itself.
_DATETIME_RE = re.compile(
    r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s*-?\s*(\d{1,2}):(\d{2})"
)

# Labels seen in real "Practical information" blocks for the same two facts.
_LOCATION_LABELS = ("venue", "place", "location")
_LANGUAGE_LABELS = ("language", "taal")

# Best-effort language-name -> ISO 639-3 code, covering the languages the
# IISG events pages actually use. Not exhaustive; unmapped names are skipped
# rather than guessed.
LANGUAGE_NAME_TO_ISO639_3 = {
    "english": "eng", "dutch": "nld", "nederlands": "nld", "french": "fra",
    "german": "deu", "spanish": "spa", "italian": "ita",
}


def _parse_datetimes(text: str) -> list[datetime]:
    results = []
    for day, month_name, year, hour, minute in _DATETIME_RE.findall(text):
        month = MONTHS.get(month_name.lower())
        if month is None:
            continue
        results.append(datetime(int(year), month, int(day), int(hour), int(minute)))
    return results


def _date_range(text: str) -> tuple[datetime | None, datetime | None]:
    found = _parse_datetimes(text)
    if not found:
        return None, None
    if len(found) == 1:
        return found[0], None
    return found[0], found[-1]


def _lines_by_br(p: Tag) -> list[str]:
    """Split a ``<p>`` into text segments at each ``<br>`` -- how the
    "Practical information" paragraph lays out one fact per line without
    using actual block elements."""
    lines: list[str] = []
    current: list[str] = []
    for node in p.contents:
        if isinstance(node, Tag) and node.name == "br":
            lines.append("".join(current).strip())
            current = []
        else:
            current.append(node.get_text() if isinstance(node, Tag) else str(node))
    lines.append("".join(current).strip())
    return [line for line in lines if line]


def _labelled_value(lines: list[str], labels: tuple[str, ...]) -> str | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    regex = re.compile(rf"^\s*({label_pattern})\s*:\s*(.+)$", re.IGNORECASE)
    for line in lines:
        m = regex.match(line)
        if m:
            value = m.group(2).strip()
            if value:
                return value
    return None


def _practical_info_lines(body: Tag | None) -> list[str]:
    if body is None:
        return []
    lines: list[str] = []
    for p in body.find_all("p"):
        lines.extend(_lines_by_br(p))
    return lines


def _clean(text: str | None) -> str | None:
    if text is None:
        return None
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip() or None


def _meta_content(soup: BeautifulSoup, *, property_: str | None = None, name: str | None = None) -> str | None:
    attrs = {"property": property_} if property_ else {"name": name}
    tag = soup.find("meta", attrs=attrs)
    return tag["content"].strip() if tag and tag.get("content") else None


def slug_from_url(url: str) -> str:
    return urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]


def parse_event_page(html: str, url: str, *, thumbnail_url: str | None = None) -> dict:
    """Parse one event detail page into a plain-dict record. ``url`` is the
    page's own URL (used to derive the slug and as ``sdo:url``);
    ``thumbnail_url`` is the cropped teaser image URL discovered while
    crawling the listing pages (see ``harvest.py``) -- the detail page
    itself only carries the uncropped original."""
    soup = BeautifulSoup(html, "lxml")

    title_el = soup.select_one("h1 .field--name-title")
    title = _clean(title_el.get_text()) if title_el else _clean(_meta_content(soup, property_="og:title"))

    summary_el = soup.select_one(".field--name-field-summary .field__item")
    summary = _clean(summary_el.get_text(" ")) if summary_el else _clean(_meta_content(soup, property_="og:description"))

    date_el = soup.select_one(".field--name-field-date .field__item")
    start, end = _date_range(date_el.get_text(" ", strip=True)) if date_el else (None, None)

    body = soup.select_one(".body .field--name-body .field__item")
    lines = _practical_info_lines(body)
    location = _clean(_labelled_value(lines, _LOCATION_LABELS))
    language_name = _clean(_labelled_value(lines, _LANGUAGE_LABELS))

    image_url = _meta_content(soup, property_="og:image")

    date_modified_text = _meta_content(soup, property_="og:updated_time")
    date_modified = None
    if date_modified_text:
        try:
            date_modified = datetime.strptime(date_modified_text, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            date_modified = None

    return {
        "url": url,
        "slug": slug_from_url(url),
        "title": title,
        "summary": summary,
        "start": start,
        "end": end,
        "location": location,
        "language_name": language_name,
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "date_modified": date_modified,
    }
