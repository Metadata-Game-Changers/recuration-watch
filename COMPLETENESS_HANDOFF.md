# Metadata Completeness — Developer Handoff Brief

A single-file web app (`completeness.html`) that measures DataCite metadata **completeness** for any repository using the Metadata Game Changers **FAIR use cases** (formerly "spirals"). It fetches live DOI metadata from the DataCite REST API, runs MGC's original `jq` queries **in the browser**, and renders per-concept completeness as a radial plot + table plus a repository-level Total index. Vanilla HTML/CSS/JS in one file, no build step. Sibling to **Re-Curation Watch**; designed to deploy alongside it without touching `index.html`.

- **Status:** working prototype, validated in-browser. Not yet integrated into the Re-Curation Watch repo.
- **Intended deploy URL:** `https://metadata-game-changers.github.io/recuration-watch/completeness.html`
- **License/attribution:** same as Re-Curation Watch (CC BY-NC 4.0), Metadata Game Changers LLC.

> Provenance note: this is a faithful browser port of `get_spiral_data()` (and `getDataFileTotal()`) from the **private** `Metadata-Game-Changers/DataCiteRepositories` repo — files `dataCiteRepositories.py` and `spirals.py`. The Python is the source of truth for methodology; this app reproduces it client-side.

---

## Files

```
completeness.html        ← the entire app (HTML+CSS+JS in one file, ~84 KB)
FAIR_spirals.json        ← the four use-case definitions as clean data (reference; ALSO embedded in the HTML)
```

`FAIR_spirals.json` is the readable source of the use-case catalog. The same data is **embedded** inside `completeness.html` as `<script id="spirals-data" type="application/json">`, so the HTML is self-sufficient and the JSON file does **not** need to be deployed. Keep them in sync if you edit queries.

The MGC logo loads from the same external CDN URL Re-Curation Watch uses (with an `onerror` graceful hide), so no image asset needs to ship.

---

## Architecture in one paragraph

On **Explore**, the app fetches a sample of a repository's DOIs from `api.datacite.org` (wrapped as `{data: [...]}`), then for each of the four FAIR use cases runs that use case's list of `jq` queries against the in-memory records using **jq-web** (jq compiled to run in the browser). Each query's top-level `select(...)` admits the records that contain the concept; **completeness = (admitted records) / (total records)**. Per-use-case aggregates (Average / Exist / Complete) and a repository **Total index** are computed in JS, mirroring the Python exactly. Everything runs client-side; there is no backend. Records are fetched once and all four use cases are scored from that single sample; the use-case dropdown/chips switch the detail view from cache without re-fetching.

---

## The engine: how the Python was ported

The Python's whole engine is `jq.all(item['jq_query'], self.metadata)` over a `{data:[...]}` object. Two decisions:

1. **Pyodide was ruled out.** The Python `jq` package is a compiled C extension (Cython binding to libjq) with no Pyodide wheel; the class also imports `doim` (not provided), `sqlite3`, `matplotlib`, etc. "Run the Python unchanged" was not viable.
2. **The queries run verbatim via jq-web.** `jq-web` is libjq compiled to WebAssembly/asm.js. MGC's exact `jq` query strings execute unchanged in the browser. Only the ~40-line scoring loop was reimplemented in JS.

### jq-web loading (this was fiddly — read before changing)

- Use the **`jq.asm.bundle.js`** build. It has the memory **embedded**, so there is **no secondary `.wasm`/`.mem` fetch** to break when loaded from a CDN. (`jq.wasm.js` needs `jq.wasm.wasm` from the same dir, which fails from a CDN; `jq.min.js` does not exist — referencing it 404s and `jq` is never defined.)
- Loaded from **jsDelivr with an unpkg fallback** (`onerror` chains to the next source).
- Readiness is confirmed with a **self-test** (`'.a'` over `{"a":1}`), so "Engine ready" means jq actually computed something, not just that the object exists.
- API used: `jq.promised.raw(JSON.stringify(input), filter, ['-c'])` → newline-delimited JSON → `split('\n')` → `JSON.parse` each. This equals Python's `jq.all()` (a list of all outputs).
- If both CDNs are blocked: download `jq.asm.bundle.js`, place it beside the HTML, and point the loader's first source at `./jq.asm.bundle.js`.

---

## Completeness math (mirrors `get_spiral_data` / `getDataFileTotal`)

For each concept in a use case:

- `matched` = number of records whose query `select(...)` admitted them (`len(results)`).
- `completeness = matched / totalRecords`, capped at 1.0 (`trimLargeCounts`). This is the per-concept score (`get_spiral_data` line ~2508).

Per use case:

- `Average` = mean of `min(completeness, 1)` across its concepts.
- `Exist` = count of concepts with completeness > 0 (`conceptExists`).
- `Complete` = count of concepts at 100% (`conceptComplete`).

Repository **Total index** (`getDataFileTotal`): concept-count-weighted average of the four use-case Averages:

```
Total = Σ(useCaseAverage × conceptCount) ÷ Σ(conceptCount)
```

Equivalent to the pooled mean of all 61 concept completeness values.

### The four FAIR use cases (61 concepts total)

| Code (internal) | Label | Concepts | Plot color |
|---|---|---|---|
| `FAIR_Text` | FAIR Text | 15 | `#E97131` |
| `FAIR_Identifiers` | FAIR Identifiers | 18 | `#0070C0` |
| `FAIR_Connections` | FAIR Connections | 18 | `#A02C93` |
| `FAIR_Contacts` | FAIR Contacts | 10 | `#4EA62E` |

(Colors come from the Python config. The full `spirals.py` has 39 use cases across several dialects; only these four DataCite-dialect ones are in scope here.)

---

## DataCite API usage

| Purpose | Endpoint / params |
|---|---|
| Repository autocomplete | `GET /clients?query={name}&page[size]=8` |
| Repository name + DOI count | `GET /clients/{id}` |
| DOIs (newest-first) | `GET /dois?client-id={id}&page[size]={min(1000,cap)}&page[number]=N&sort=-updated&affiliation=true&publisher=true` |
| DOIs (random sample) | `GET /dois?client-id={id}&page[size]={min(1000,cap)}&affiliation=true&publisher=true&random=true&disable-facets=true` |

Records are wrapped as `{data: allRecords}` before scoring (matches `get_spiral_data` line ~2423).

### `affiliation=true&publisher=true` are REQUIRED

By default DataCite returns `publisher` as a string and `affiliation` as bare strings. With these params they become **structured objects** (`publisher: {name, publisherIdentifier, …}`, `affiliation: [{name, affiliationIdentifier, …}]`). Several FAIR queries read those nested fields (publisher identifier, affiliation names/identifiers), so **without these params those concepts silently under-count**. Re-Curation Watch's `loadRepository` does NOT currently send these — see Integration below.

### Random sampling + dedup (important)

`random=true` gives a representative sample (avoids bias toward recently-updated records). But per DataCite docs, with `random=true` the **`sort` and `page[number]` params are ignored** — each request is an independent draw. So:

- A single request returns up to `page[size]` distinct records.
- To build a sample larger than one page, fire **multiple** random requests and **deduplicate by DOI id** (`record.id`); repeats across draws are discarded.
- Stop when: target `cap` reached · whole repo collected (`meta.total`) · a fresh draw adds **zero** new DOIs (saturation) · hard guard (30 requests).
- Consequence: when the repo is smaller than `cap`, or random overlap saturates, you legitimately get **fewer than `cap`** records. The selection summary reports the actual count.

`page[size]` max is 1000; `page[number]` pagination tops out at 10,000 records (10×1000). Beyond that needs cursor pagination (not implemented — see Open items).

---

## CRITICAL gotchas (hard-won; do not regress)

1. **jq object-value grammar — bare `if…end` is a parse error.** MGC's queries write `count: if (X // null) != null then 1 else 0 end`. In jq an object value must be a *term*, and `if…end` is an *expression*, so `{count: if … end}` **fails to parse** in stricter/older jq (including the one in jq-web). The newer libjq behind the Python `jq` package tolerates it, which is why it was never caught upstream. **Fix: wrap the if-expression in parentheses** → `count: (if … end)`. This was applied to 10 queries in the embedded catalog. Symptom when broken: the whole concept errors regardless of data (shown as red "query error").

2. **Unguarded `has()` on a non-object throws and aborts the whole stream.** Queries like `select((.attributes.publisher | has("name") …))` throw if `publisher` is a string/null (jq `has` requires object/array), and one error aborts the entire `.data[]` stream → the concept comes back empty. **Fix: lead with a `type == "object"` guard** (jq `and` short-circuits, so the `has()` is never reached on non-objects) → `select((.attributes.publisher | type == "object") and (.attributes.publisher | has("name") and .name != null))`. Applied to the publisher/types/publisher-identifier selects. Same defect class exists upstream.

3. **The above two fixes live only in this prototype's embedded catalog and in `FAIR_spirals.json` — NOT in `spirals.py`.** They are real bugs in the Python source that happen to work under its lenient jq. Mirror them upstream (see Open items).

4. **`file://` blocks fetch.** Opening the HTML by double-click makes browsers refuse outbound requests ("Failed to fetch"). **Serve over http** (`python3 -m http.server`). The page detects `file://` and says so.

5. **The engine self-test gates "ready."** Don't remove it; it's what distinguishes "jq object exists" from "jq actually runs."

6. **Dedup by `record.id` whenever multiple DOI requests are made**, not just in random mode (harmless in page mode, essential in random).

---

## UI structure

- **Brand top bar** — ported from Re-Curation Watch: MGC logo + Montserrat wordmark ("METADATA COMPLETENESS") + links to Re-Curation Watch and metadatagamechangers.com. Google Fonts: Inter / IBM Plex Mono / Montserrat.
- **Hero bar** — ported from RCW (`#f0eaf5` tint, `#9167b0` border). Repository search with **autocomplete** (`/clients?query=`) + **Explore →**. Only the repository selector is enabled (RCW's secondary Type/Query row was intentionally not ported). The hero-secondary row holds this tool's controls: **Use case** detail selector, **Max** records, **Random sample** toggle.
- **Selection summary** strip (below hero) — repository name + client ID, records analyzed, sampling mode, and "of N in repository".
- **Total index card** — big repository index + four clickable per-use-case chips (color-coded).
- **Detail grid** — radial plot (shaded polygon in the use case's color, no vertex markers, alphabetized concepts) + concept table (Concept · Record % · completeness bar; counts in tooltips; errored concepts marked red).
- **Progress bar** — indeterminate during engine load and random fetch; determinate `records ÷ cap` for newest-first fetch and `query N of 61` while scoring.
- **API call** line — shows the exact URL used (and "N random draws, deduplicated by DOI").

### Terminology

User-visible text says **"use case"** (per current MGC terminology). Internal JS identifiers still say `spiral` (`SPIRALS`, `runSpiral`, `populateSpirals`, `SPIRAL_COLORS`, `spiral.code`) — not visible, left as-is to avoid churn. If you rename in code, rename consistently.

---

## Open items / integration roadmap

**Mirror the query fixes upstream (highest value).** Patch `spirals.py` in `DataCiteRepositories`:
- Parenthesize every bare `count: if … end` → `count: (if … end)`.
- Add `type == "object"` guards to unguarded `has()` selects (publisher, types, publisher-identifier group).
These make the queries robust under any jq, not just the lenient Python binding.

**Converge with Re-Curation Watch.**
- Both tools want the same repository search component (the hero autocomplete is already copied here). Factor it into something shared, or at least keep them consistent.
- If completeness is folded into `index.html`, **reuse the in-memory `allDOIs`** instead of re-fetching — BUT first add `affiliation=true&publisher=true` to RCW's `loadRepository` fetch, or the publisher/affiliation concepts will under-count. (Verify this doesn't change RCW's existing card rendering — it reads string/`name` fields that remain present.)
- Optional: single-DOI / prefix completeness (the hero currently supports repository only).

**Deployment.** Drop `completeness.html` into the repo root on `main` next to `index.html` (don't touch `index.html`). The existing "Deploy from a branch (main/root)" picks it up; no Actions, no settings changes. Soft cross-link already present (brand-bar link to RCW).

**Nice-to-haves.**
- Cursor pagination (`page[cursor]`) to score repos larger than 10,000 records.
- Validate the Total index against the Python's `getDataFileTotal()` for the same repo + sample size as a faithfulness check (expect slight wobble run-to-run because random sampling).
- Brand wordmark name is a placeholder ("Metadata Completeness") — confirm the intended product name.
- Echo the Total index and/or current use case into the selection summary if useful.

**Verification caveats.** The engine/network couldn't be exercised in the authoring sandbox (no WASM, no egress); all live behavior (jq-web init, DataCite fetch, scoring) was confirmed in the user's browser. Re-test after any change to the loader, fetch, or queries.

---

## Quick start (local)

```
# from the folder containing completeness.html
python3 -m http.server 8000
# open http://localhost:8000/completeness.html
# Explore "sjyq.oozvia" (or search a repository by name)
```
