"""Command-line entry point: ``python -m events_etl.cli``."""

from __future__ import annotations

import argparse
import itertools
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from rdflib import Graph

from . import harvest
from .fixtures import load_fixture
from .parse import parse_event_page
from .pipeline import process_event
from .prefixes import DEFAULT_GRAPH, NAMESPACE_BINDINGS

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "static" / "events" / "sourceData"


def _iter_fixture_records(slug: str | None, harvested_at: datetime):
    for path in sorted(FIXTURES_DIR.glob("*.html")):
        if slug and path.stem != slug:
            continue
        fixture = load_fixture(path)
        record = parse_event_page(fixture["html"], fixture["url"], thumbnail_url=fixture["thumbnail_url"])
        record["harvested_at"] = harvested_at
        yield record


def _iter_web_records(slug: str | None, delay: float, harvested_at: datetime):
    session = requests.Session()
    for entry in harvest.iter_event_listing_entries(session=session, delay=delay):
        record_slug = entry["url"].rstrip("/").rsplit("/", 1)[-1]
        if slug and record_slug != slug:
            continue
        html = harvest.fetch_event_html(entry["url"], session=session)
        record = parse_event_page(html, entry["url"], thumbnail_url=entry["thumbnail_url"])
        record["harvested_at"] = harvested_at
        yield record


def build_graph(records) -> Graph:
    g = Graph(identifier=DEFAULT_GRAPH)
    for prefix, ns in NAMESPACE_BINDINGS.items():
        g.bind(prefix, ns)
    for record in records:
        process_event(record, g)
    return g


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IISG events ETL")
    parser.add_argument("--source", choices=["fixtures", "web"], default="fixtures")
    parser.add_argument("--slug", help="Only process the event whose URL slug matches this")
    parser.add_argument("--limit", type=int, help="Stop after this many events")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between requests in --source web (default: 0.5)")
    parser.add_argument("--out", type=Path, help="Output Turtle file (stdout if omitted)")
    args = parser.parse_args(argv)

    harvested_at = datetime.now(timezone.utc)

    if args.source == "fixtures":
        records = _iter_fixture_records(args.slug, harvested_at)
    else:
        records = _iter_web_records(args.slug, args.delay, harvested_at)

    if args.limit:
        records = itertools.islice(records, args.limit)

    g = build_graph(records)

    turtle = g.serialize(format="turtle")
    if args.out:
        args.out.write_text(turtle, encoding="utf-8")
        print(f"Wrote {len(g)} triples to {args.out}", file=sys.stderr)
    else:
        print(turtle)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
