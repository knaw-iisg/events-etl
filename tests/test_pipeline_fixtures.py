"""Runs every static/events/sourceData fixture through the full pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest
from rdflib import Graph, Namespace, URIRef

from events_etl.fixtures import load_fixture
from events_etl.parse import parse_event_page
from events_etl.pipeline import process_event

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "static" / "events" / "sourceData"
SDO = Namespace("https://schema.org/")


def _fixture_paths():
    return sorted(FIXTURES_DIR.glob("*.html"))


@pytest.mark.parametrize("path", _fixture_paths(), ids=lambda p: p.stem)
def test_event_processes_without_error(path: Path):
    fixture = load_fixture(path)
    record = parse_event_page(fixture["html"], fixture["url"], thumbnail_url=fixture["thumbnail_url"])
    g = Graph()
    item = process_event(record, g)
    assert item is not None
    assert len(g) > 0
    assert (item, None, SDO.Event) in g
    assert (item, SDO.name, None) in g
    g.serialize(format="nt")


def test_single_date_event_has_start_but_no_end():
    path = FIXTURES_DIR / "book-presentation-womens-labour-activism-eastern-europe-and-beyond.html"
    fixture = load_fixture(path)
    record = parse_event_page(fixture["html"], fixture["url"], thumbnail_url=fixture["thumbnail_url"])
    g = Graph()
    item = process_event(record, g)
    assert item == URIRef("https://iisg.amsterdam/id/event/book-presentation-womens-labour-activism-eastern-europe-and-beyond")
    starts = list(g.objects(item, SDO.startDate))
    ends = list(g.objects(item, SDO.endDate))
    assert len(starts) == 1
    assert str(starts[0]) == "2026-10-06T16:00:00"
    assert ends == []


def test_ranged_event_has_start_and_end():
    path = FIXTURES_DIR / "documentary-slaves-empire.html"
    fixture = load_fixture(path)
    record = parse_event_page(fixture["html"], fixture["url"], thumbnail_url=fixture["thumbnail_url"])
    g = Graph()
    item = process_event(record, g)
    assert str(next(g.objects(item, SDO.startDate))) == "2026-07-21T16:00:00"
    assert str(next(g.objects(item, SDO.endDate))) == "2026-07-21T18:00:00"


def test_location_extracted_from_free_text_practical_info():
    path = FIXTURES_DIR / "cgm-workshop-migration-researchers-and-public-debate.html"
    fixture = load_fixture(path)
    record = parse_event_page(fixture["html"], fixture["url"], thumbnail_url=fixture["thumbnail_url"])
    g = Graph()
    item = process_event(record, g)
    place = next(g.objects(item, SDO.location))
    assert (place, None, SDO.Place) in g
    assert str(next(g.objects(place, SDO.name))) == "IISH, Cruquiusweg 31, Amsterdam"


def test_language_name_resolves_to_lexvo_iri():
    path = FIXTURES_DIR / "exhibition-objects-remember.html"
    fixture = load_fixture(path)
    record = parse_event_page(fixture["html"], fixture["url"], thumbnail_url=fixture["thumbnail_url"])
    g = Graph()
    item = process_event(record, g)
    assert (item, SDO.inLanguage, URIRef("http://lexvo.org/id/iso639-3/eng")) in g


def test_image_and_thumbnail_nested_under_image_object():
    path = FIXTURES_DIR / "auditory-lens-social-resilience-post-colonial-south-africa.html"
    fixture = load_fixture(path)
    record = parse_event_page(fixture["html"], fixture["url"], thumbnail_url=fixture["thumbnail_url"])
    g = Graph()
    item = process_event(record, g)
    image = next(g.objects(item, SDO.image))
    assert (image, None, SDO.ImageObject) in g
    content_url = str(next(g.objects(image, SDO.contentUrl)))
    assert content_url.startswith("https://iisg.amsterdam/files/2026-06/")
    thumbnail = next(g.objects(image, SDO.thumbnail))
    assert (thumbnail, None, SDO.ImageObject) in g
    thumbnail_url = str(next(g.objects(thumbnail, SDO.contentUrl)))
    assert "styles/12x7_524w" in thumbnail_url
