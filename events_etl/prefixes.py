"""Namespace/prefix declarations used throughout the pipeline."""

from rdflib import Namespace

BASE = "https://iisg.amsterdam/"
ID = BASE + "id/"

# Real, locally-minted resources (not controlled-vocabulary authority terms
# -- those live under a separate .../authority/ base in the sibling repos).
EVENT = Namespace(ID + "event/")
DATASET = Namespace(ID + "dataset/")

# External vocabularies
SDO = Namespace("https://schema.org/")
LEXVO_ISO639_3 = Namespace("http://lexvo.org/id/iso639-3/")

SITE_BASE = "https://iisg.amsterdam"

DEFAULT_GRAPH = "https://iisg.amsterdam/graph/events"

# All namespaces, used for Turtle serialization prefixes.
NAMESPACE_BINDINGS = {
    "event": EVENT,
    "dataset": DATASET,
    "sdo": SDO,
    "iso639-3": LEXVO_ISO639_3,
}
