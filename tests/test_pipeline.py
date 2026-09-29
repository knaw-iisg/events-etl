"""Unit tests using small hand-built HTML snippets (independent of the real
fixtures), covering edge cases: missing location/language, no date, and the
NDE-AP enrichment applied to every event."""

from __future__ import annotations

from datetime import datetime, timezone

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import XSD

from events_etl.parse import parse_event_page
from events_etl.pipeline import process_event

SDO = Namespace("https://schema.org/")


def _page(*, title="Test Event", date_field="", practical="", summary="A test event.") -> str:
    return f"""
    <html><head>
      <meta property="og:title" content="{title}" />
      <meta property="og:description" content="{summary}" />
    </head><body>
      <h1><span class="field field--name-title">{title}</span></h1>
      <div class="content-wrapper"><div class="textual">
        <div class="date">
          <div class="field field--name-field-date field__items">
            <div class="field__item">{date_field}</div>
          </div>
        </div>
        <div class="body">
          <div class="field field--name-field-summary field__items">
            <div class="field__item"><p>{summary}</p></div>
          </div>
          <div class="clearfix field field--name-body field__items">
            <div class="field__item">{practical}</div>
          </div>
        </div>
      </div></div>
    </body></html>
    """


def test_event_with_no_date_field_has_no_start_or_end():
    html = _page(date_field="")
    record = parse_event_page(html, "https://iisg.amsterdam/en/events/test-event")
    g = Graph()
    item = process_event(record, g)
    assert item == URIRef("https://iisg.amsterdam/id/event/test-event")
    assert (item, SDO.startDate, None) not in g
    assert (item, SDO.endDate, None) not in g


def test_event_with_no_practical_info_has_no_location_or_language():
    html = _page(date_field="1 January 2026 10:00", practical="<p>Just a paragraph.</p>")
    record = parse_event_page(html, "https://iisg.amsterdam/en/events/test-event")
    g = Graph()
    item = process_event(record, g)
    assert (item, SDO.location, None) not in g
    assert (item, SDO.inLanguage, None) not in g


def test_unrecognized_language_name_is_not_guessed():
    html = _page(
        date_field="1 January 2026 10:00",
        practical="<p><strong>Language</strong>: Esperanto<br/></p>",
    )
    record = parse_event_page(html, "https://iisg.amsterdam/en/events/test-event")
    g = Graph()
    item = process_event(record, g)
    assert (item, SDO.inLanguage, None) not in g


def test_record_with_no_slug_is_skipped():
    g = Graph()
    item = process_event({"slug": "", "title": "x"}, g)
    assert item is None
    assert len(g) == 0


def test_nde_ap_dataset_link_and_typed_sd_date_published():
    html = _page(date_field="1 January 2026 10:00")
    record = parse_event_page(html, "https://iisg.amsterdam/en/events/test-event")
    record["harvested_at"] = datetime(2026, 1, 1, tzinfo=timezone.utc)
    g = Graph()
    item = process_event(record, g)

    assert (item, SDO.isPartOf, URIRef("https://iisg.amsterdam/id/dataset/events")) in g
    dates = list(g.objects(item, SDO.sdDatePublished))
    assert dates
    assert dates[0].datatype == XSD.dateTime
    assert str(dates[0]) == "2026-01-01T00:00:00+00:00"


def test_dataset_description_has_bilingual_names():
    html = _page(date_field="1 January 2026 10:00")
    record = parse_event_page(html, "https://iisg.amsterdam/en/events/test-event")
    g = Graph()
    process_event(record, g)

    dataset = URIRef("https://iisg.amsterdam/id/dataset/events")
    names = {(str(o), o.language) for o in g.objects(dataset, SDO.name)}
    assert ("IISH Events", "en") in names
    assert ("IISG Evenementen", "nl") in names
