"""Namespace/prefix declarations used throughout the pipeline."""

from rdflib import Namespace

BASE = "https://iisg.amsterdam/"
ID = BASE + "id/"

# Real, locally-minted resources (not controlled-vocabulary authority terms
# -- those live under a separate .../authority/ base in the sibling repos).
EVENT = Namespace(ID + "event/")
DATASET = Namespace(ID + "dataset/")
# Venues mentioned in events' free-text "Practical information" -- keyed by
# a slug of the location string itself (see pipeline.py), not geocoded. Not
# the same IRI space as authorities-etl's authority/place/ (geographic
# subject-heading terms from MARC 151); this is deliberately named "venue"
# rather than reusing "place" to keep the two visually distinct wherever
# both graphs are browsed together.
PLACE = Namespace(ID + "place/")

# External vocabularies
SDO = Namespace("https://schema.org/")
LEXVO_ISO639_3 = Namespace("http://lexvo.org/id/iso639-3/")

SITE_BASE = "https://iisg.amsterdam"

DEFAULT_GRAPH = "https://iisg.amsterdam/graph/events"

# All namespaces, used for Turtle serialization prefixes.
NAMESPACE_BINDINGS = {
    "event": EVENT,
    "dataset": DATASET,
    "place": PLACE,
    "sdo": SDO,
    "iso639-3": LEXVO_ISO639_3,
}
