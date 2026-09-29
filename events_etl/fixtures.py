"""Loading/saving ``static/events/sourceData/*`` fixtures: a raw detail-page
HTML file plus a JSON sidecar for the two facts that only exist on the
listing pages the HTML was reached from (``url``, ``thumbnail_url``) -- see
``harvest.py``."""

from __future__ import annotations

import json
from pathlib import Path


def save_fixture(directory: Path, slug: str, html: str, *, url: str, thumbnail_url: str | None) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{slug}.html").write_text(html, encoding="utf-8")
    (directory / f"{slug}.json").write_text(
        json.dumps({"url": url, "thumbnail_url": thumbnail_url}, indent=2), encoding="utf-8",
    )


def load_fixture(html_path: Path) -> dict:
    meta = json.loads(html_path.with_suffix(".json").read_text(encoding="utf-8"))
    return {
        "html": html_path.read_text(encoding="utf-8"),
        "url": meta["url"],
        "thumbnail_url": meta.get("thumbnail_url"),
    }
