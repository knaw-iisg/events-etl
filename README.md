# events-etl

Scrapes IISG's events pages ([current](https://iisg.amsterdam/en/events),
[archive](https://iisg.amsterdam/en/events/archive)) and maps them to RDF,
conforming to the [NDE Schema.org Application Profile](https://docs.nde.nl/schema-profile/)
(SCHEMA-AP-NDE) -- same pattern as the sibling
[biblio-etl](https://github.com/knaw-iisg/biblio-etl),
[archive-etl](https://github.com/knaw-iisg/archive-etl),
[findingaid-etl](https://github.com/knaw-iisg/findingaid-etl) and
[authorities-etl](https://github.com/knaw-iisg/authorities-etl) repos, except
the source here is scraped HTML rather than MARC/OAI-PMH or EAD.

Unlike those repos, events have no persistent identifier or machine-readable
metadata of their own -- there is no `<script type="application/ld+json">`
or microdata on the page, and no separate API. Everything is mined from the
rendered Drupal markup: the event's own URL slug becomes its identifier, and
"Practical information" facts (venue, language) are extracted from free text
with a best-effort label match (`Venue:`/`Place:`/`Location:`,
`Language:`) -- confirmed inconsistent across real pages (the same fact
under different labels, or simply absent), so nothing is guessed when a
label isn't found.

## Public instance

This pipeline's output is merged with six others into a single public
knowledge graph, browsable at **https://kb.zijdeman.nl** and queryable
directly at **https://sparql.zijdeman.nl** (or via QLever's own query UI
at **https://kg.zijdeman.nl**) -- see
[iisg-kb-viewer](https://github.com/knaw-iisg/iisg-kb-viewer) and
[triplestore](https://github.com/knaw-iisg/triplestore).

## Field mapping

| Source | RDF |
|---|---|
| event detail page URL slug | forms the event's URI, `event:<slug>` |
| `<h1>` title | `sdo:name` (`@en` -- only the site's English pages are scraped) |
| Summary field (falls back to `og:description`) | `sdo:description` (`@en`) |
| Date field (`"6 October 2026 16:00"`, or a start/end range) | `sdo:startDate` / `sdo:endDate` (naive local datetime -- the site never states a timezone; see Known gaps) |
| `og:updated_time` | `sdo:dateModified` |
| `og:image` (full-size original) | `sdo:image`, an `sdo:ImageObject` |
| Listing-page teaser image (Drupal image style `12x7_524w`, only available while crawling the listing, not the detail page) | `sdo:thumbnail` nested under that `sdo:ImageObject` |
| `Venue:`/`Place:`/`Location:` line in "Practical information" | `sdo:location`, an `sdo:Place` with only `sdo:name` (best-effort free text, no geocoding) |
| `Language:` line, when it names a language this repo recognises | `sdo:inLanguage`, a `lexvo.org/id/iso639-3/` IRI (same vocabulary the sibling repos use) |
| event's own URL | `sdo:url` |

## Known gaps

- **No timezone on dates.** The site states times like "16:00" with no UTC
  offset; `sdo:startDate`/`sdo:endDate` are emitted as timezone-naive
  `xsd:dateTime` (implicitly Europe/Amsterdam local time). Fine for display,
  not safe to compare across timezones as-is.
- **`sdo:location` is free text, not geocoded.** ~30% of events state a
  venue at all; of those, several distinct strings all refer to the same
  physical IISG building (`"IISG, Cruquiusweg 31 Amsterdam"`,
  `"IISH, Cruquiusweg 31, Amsterdam"`, `"International Institute of Social
  History, Cruquiusweg 31, 1019 AT Amsterdam"`, ...) -- not deduplicated to
  a shared `sdo:Place` IRI. Would need either a minted IISG venue IRI or a
  geocoding pass.
- **No `sdo:organizer`.** IISG itself isn't minted as an `sdo:Organization`
  anywhere in this pipeline family yet.
- **Only the English (`/en/`) site is scraped.** The Dutch version exists at
  the same slugs under `/nl/events/` but isn't harvested -- v1 scope, per
  the URLs the user gave.
- **NDE Dataset Register registration is incomplete** -- same open
  `# TODO(IISG)` (license, catalog, access-rights IRIs) as every sibling
  repo's dataset node; see `nde_ap.py`.

## Install

```bash
python -m venv .venv
.venv/bin/pip install -e ".[test]"
```

## Run

```bash
# Sample pages under static/events/sourceData/:
python -m events_etl.cli --source fixtures --out events.ttl

# Live crawl (current + full paginated archive, ~170 events, a few seconds):
python -m events_etl.cli --source web --out events.ttl

# One event only, by URL slug:
python -m events_etl.cli --source web --slug documentary-slaves-empire
```

## Test

```bash
.venv/bin/pytest
```
