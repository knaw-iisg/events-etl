"""NDE Schema.org Application Profile (SCHEMA-AP-NDE) enrichment, applied to
every event after its own fields are mapped.

Reference: https://docs.nde.nl/schema-profile/ -- per-item (``Event``)
requirements used here: persistent URI (events are minted at
``event:<slug>``), a language-tagged ``sdo:name``/``sdo:description``
(handled directly in ``pipeline.py``, tagged "en" since only the site's
English pages are scraped), and ``sdo:sdDatePublished``.

What this deliberately does *not* do: register the Events dataset in the NDE
Dataset Register. That needs a license IRI, catalog IRI and access-rights
statement that aren't derivable from the scraped pages -- see the
``# TODO(IISG)`` marker below, same open question as the sibling repos'
dataset nodes. A minimal ``sdo:Dataset`` node is still emitted so that
``sdo:isPartOf`` resolves to something.
"""

from __future__ import annotations

from datetime import datetime, timezone

from rdflib import RDF, Graph, Literal, URIRef
from rdflib.namespace import XSD

from .prefixes import DATASET, SDO

DATASET_IRI = DATASET["events"]


def _emit_dataset_description(g: Graph) -> None:
    if (DATASET_IRI, RDF.type, SDO.Dataset) in g:
        return
    g.add((DATASET_IRI, RDF.type, SDO.Dataset))
    g.add((DATASET_IRI, SDO.name, Literal("IISG Evenementen", lang="nl")))
    g.add((DATASET_IRI, SDO.name, Literal("IISH Events", lang="en")))
    g.add((DATASET_IRI, SDO.description, Literal(
        "Aankondigingen en archief van evenementen van het Internationaal "
        "Instituut voor Sociale Geschiedenis (IISG).", lang="nl",
    )))
    # TODO(IISG): sdo:license (a license IRI), sdo:includedInDataCatalog (the
    # NDE Dataset Register catalog IRI this dataset is registered under) and
    # sdo:accessRights aren't published anywhere on the events pages
    # themselves and shouldn't be guessed -- fill in once known.


def enrich(item: URIRef, g: Graph, *, dataset_iri: URIRef = DATASET_IRI, sd_date_published: datetime | None = None) -> None:
    g.add((item, SDO.sdDatePublished, Literal(
        (sd_date_published or datetime.now(timezone.utc)).isoformat(), datatype=XSD.dateTime,
    )))
    g.add((item, SDO.isPartOf, dataset_iri))
    _emit_dataset_description(g)
