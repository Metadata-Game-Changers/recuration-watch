# Recovering the per-record `values` (and `count`) from the use-case queries

The completeness tool scores **presence** — for each concept, the share of records that contain
it. To do that it only needs a count of matching records, so at runtime it deliberately discards
the richer per-record output the queries can produce. This note explains what that richer output
is and how a future tool can recover it. **No data or query was lost** — the full queries are
stored intact; only the live scorer ignores part of their output.

## What the full queries produce

Every use-case query in the catalog has the shape:

```
.data[] | select(<EXPR>) | { id: .id, concept: "<name>", count: (<count>), values: (<values>) }
```

Run **as written**, a query emits **one JSON object per matching record**:

| field     | meaning |
|-----------|---------|
| `id`      | the DOI id of the record |
| `concept` | the concept name (constant for the query) |
| `count`   | how many times the concept occurs in that record (e.g. number of matching array elements) |
| `values`  | the actual value(s) — a scalar or an array (e.g. all `relatedIdentifier`s, all author names) |

Example (one record, the "Cites" concept):

```json
{"id":"10.1/a","concept":"Cites","count":1,"values":["10.x/1"]}
```

So a full run over `{data: [...records...]}` yields a stream of these objects — exactly the data
you'd want for value-level analysis (vocabularies used, identifier schemes present, distinct
value counts, occurrence histograms, etc.).

## Where the queries live (unchanged)

- **`FAIR_spirals.json`** — the readable catalog: an array of use cases, each with
  `{title, code, dialect, description, items:[{concept, jq_query}]}`.
- **`completeness.html`** — the same array embedded as `<script id="spirals-data" type="application/json">`.

Both contain the **complete** `jq_query` strings, including the `count`/`values` projection. They
are the source to read from.

## Why the live tool drops `values`

In `completeness.html`, `scoreAllSpirals()` calls `countExpr(query)`, which strips everything from
the first `{` (the projection) and counts the records the `select(...)` admits:

```
.data[] | select(<EXPR>)        ->  [ .data[] | select(<EXPR>) ] | length
```

This is equivalent to `len(results)` for scoring but avoids building the (potentially large)
`values` arrays for thousands of records — the dominant cost on big samples. Recovering values
means **not** applying `countExpr`: run the original `jq_query` instead.

## How to recover the values

### In the browser (jq-web, as this tool loads it)

```js
// records = array of DataCite DOI objects (fetch with &affiliation=true&publisher=true — see below)
async function jqAll(records, jqQuery){
  const out = await jq.promised.raw(JSON.stringify({ data: records }), jqQuery, ['-c']);
  return out ? out.split('\n').filter(l => l.trim()).map(l => JSON.parse(l)) : [];
}

// e.g. every record's related-identifier values for one concept:
const rows = await jqAll(records, spiral.items[i].jq_query);   // [{id, concept, count, values}, ...]
```

(This is the original `jqAll` the scorer used before it switched to count-only.)

### On the command line

```sh
# data.json = { "data": [ ...records... ] }
jq -c "$JQ_QUERY" data.json     # one {id, concept, count, values} object per matching record
```

### Aggregating values (example: distinct values + occurrence counts for a concept)

```sh
jq -c "$JQ_QUERY" data.json \
  | jq -s '{ concept: .[0].concept,
             records_with: length,
             total_occurrences: (map(.count) | add),
             distinct_values: ([.[].values] | flatten | unique | length),
             value_histogram: ([.[].values] | flatten | group_by(.) | map({value: .[0], n: length})) }'
```

## Gotchas to carry over (same as the scoring tool)

- **Fetch with `&affiliation=true&publisher=true`.** Without them DataCite returns `publisher` as a
  string and `affiliation` as bare strings; several queries read nested fields and will otherwise
  under-report. (`&resource-type-id=` and `&query=` optionally filter the set.)
- **jq strictness.** The catalog queries already include the two fixes the lenient Python `jq`
  hid: bare `count: if … end` is parenthesized → `count: (if … end)`, and `has()` calls are guarded
  with `type == "object"`. Validate any new/edited query under a stricter `jq` (jq-1.6 is a good
  proxy for jq-web) before relying on it.
- **`spirals.py` is the methodology source of truth** (private `Metadata-Game-Changers/DataCiteRepositories`).
  Port query strings verbatim; keep `FAIR_spirals.json` and the embedded catalog in sync with it.

## TL;DR

The `values`/`count` capability is fully preserved in the query catalog. To use it: read the
`jq_query` from `FAIR_spirals.json` (or the embedded `spirals-data`), run it **whole** (do not
strip the projection) over `{data: records}`, and read `{id, concept, count, values}` per matching
record.
