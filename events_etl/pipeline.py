"""Record dict (see ``parse.parse_event_page``) -> RDF pipeline."""

from __future__ import annotations

import re

from rdflib import RDF, BNode, Graph, Literal, URIRef
from rdflib.namespace import XSD

from . import nde_ap
from .parse import LANGUAGE_NAME_TO_ISO639_3
from .prefixes import EVENT, LEXVO_ISO639_3, PLACE, SDO


def _slugify(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def process_event(record: dict, g: Graph) -> URIRef | None:
    """Process one event record (as produced by ``parse.parse_event_page``)
    into ``g``. Returns the minted event IRI, or ``None`` if the record has
    no usable slug."""
    slug = record.get("slug")
    if not slug:
        return None

    item = EVENT[slug]
    g.add((item, RDF.type, SDO.Event))

    if record.get("title"):
        g.add((item, SDO.name, Literal(record["title"], lang="en")))
    if record.get("summary"):
        g.add((item, SDO.description, Literal(record["summary"], lang="en")))
    if record.get("url"):
        g.add((item, SDO.url, URIRef(record["url"])))

    if record.get("start"):
        g.add((item, SDO.startDate, Literal(record["start"].isoformat(), datatype=XSD.dateTime)))
    if record.get("end"):
        g.add((item, SDO.endDate, Literal(record["end"].isoformat(), datatype=XSD.dateTime)))
    if record.get("date_modified"):
        g.add((item, SDO.dateModified, Literal(record["date_modified"].isoformat(), datatype=XSD.dateTime)))

    if record.get("location"):
        slug = _slugify(record["location"])
        if slug:
            place = PLACE[slug]
            g.add((place, RDF.type, SDO.Place))
            g.add((place, SDO.name, Literal(record["location"])))
            g.add((item, SDO.location, place))

    language_code = LANGUAGE_NAME_TO_ISO639_3.get((record.get("language_name") or "").lower())
    if language_code:
        g.add((item, SDO.inLanguage, LEXVO_ISO639_3[language_code]))

    image_url = record.get("image_url")
    thumbnail_url = record.get("thumbnail_url")
    if image_url:
        image = BNode()
        g.add((image, RDF.type, SDO.ImageObject))
        g.add((image, SDO.contentUrl, URIRef(image_url)))
        if thumbnail_url:
            thumbnail = BNode()
            g.add((thumbnail, RDF.type, SDO.ImageObject))
            g.add((thumbnail, SDO.contentUrl, URIRef(thumbnail_url)))
            g.add((image, SDO.thumbnail, thumbnail))
        g.add((item, SDO.image, image))
    elif thumbnail_url:
        image = BNode()
        g.add((image, RDF.type, SDO.ImageObject))
        g.add((image, SDO.contentUrl, URIRef(thumbnail_url)))
        g.add((item, SDO.image, image))

    nde_ap.enrich(item, g, sd_date_published=record.get("harvested_at"))

    return item
