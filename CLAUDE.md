# CLAUDE.md

Guidance for working in this repository.

## What this is

Static, single-file web apps for Metadata Game Changers, deployed via GitHub Pages
(deploy from a branch — `main` / root; no build step, no Actions). Each app is one
self-contained HTML file with inline CSS + vanilla JS — no framework, no bundler.

- `index.html` — the **site homepage**: the one-page tools overview (formerly `tools.html`;
  that filename is now a redirect stub kept for old links).
- `recurationWatch.html` — **Re-Curation Watch** (the original tool; lived at `index.html`
  until July 2026 — the DOI 10.60872/recurationWatch should resolve here).
- `completeness.html` — **Metadata Completeness**: scores a DataCite repository against
  MGC FAIR/DataCite/Project use cases. Runs MGC's `jq` queries **in the browser** via
  jq-web (jq compiled to WASM) and fetches live DOIs from `api.datacite.org`.
- `repo-activity.html` — repository activity view.
- `metadataConnectivity.html` — **Metadata Connectivity**: measures identifier connectivity
  (ORCID/ROR/funder/publisher/rights identifiers) for a DataCite repository; bar drill-downs
  hand names identified < 100% to the retrievers (affiliations/funders/publishers → ROR
  Retriever, people → ORCID Retriever).
- `rorRetriever.html` — **ROR Retriever**: browser port of `RORRetriever.py`
  (Metadata-Game-Changers/RORRetriever) — matches affiliation strings via the ROR affiliation
  API. Keep the core affiliation-strategy logic (chosen/`--noacronyms`/`--max` semantics, TSV
  columns and file naming) faithful to the Python; web-side enhancements (e.g. the QUERY
  keyword-search fallback, source-dataset strip) are fine and candidates to port back.
  Accepts handoffs via localStorage key `ror-retriever-input` (`?input=stored`) or
  `#affiliations=…`, with `auto=1` to run.
- `orcidRetriever.html` — **ORCID Retriever**: browser port of the name→ORCID flow in
  `getORCIDs.py` (Metadata-Game-Changers/ORCID-Tools) — searches the public ORCID API by
  parsed family/given name and shows each candidate iD with its most recent employment and
  journal for disambiguation. Anonymous API (no token). Accepts handoffs via localStorage
  key `orcid-retriever-input` (`?input=stored`) or `#names=…`, with `auto=1` to run.
- `repositoryHistory.html` — **Repository History** (prototype): samples each **registered
  year** (min–max, auto-detected via two `sort=created` requests — the API ignores
  `sort=registered` and returns no facets), scores every year with the completeness engine,
  and plots use-case lines over time. Scores are **cohort** views (records as they are
  *today*, incl. re-curation) — keep that caveat in any copy. Unlike completeness.html it
  **fetches** `FAIR_spirals.json` at boot instead of embedding it; its scoring functions
  are ports from completeness.html — keep them in sync.
- `FAIR_spirals.json` — readable catalog of the use cases (also **embedded** inside
  `completeness.html`; keep the two in sync).
- `tips.html` — **generated** collection of every tool's while-you-wait tips. Never edit by
  hand: edit the tips array in the tool page, then `python3 makeTipsPage.py` (use `--check`
  to detect drift).
- `COMPLETENESS_HANDOFF.md`, `REPO_ACTIVITY_HANDOFF.md` — design/handoff notes; read the
  relevant one before deep work on that tool.

## Running / previewing locally

`file://` blocks the DataCite fetch — **always serve over http**:

```
python3 -m http.server 8000
# open http://localhost:8000/completeness.html
```

Example repository to test with: client ID `sjyq.oozvia` (Metadata Game Changers).
`.claude/launch.json` (untracked) configures the preview server. Don't commit `.DS_Store`.

## Use cases (the `completeness.html` catalog)

- **Source of truth is `spirals.py`** in the private `Metadata-Game-Changers/DataCiteRepositories`
  methodology (locally cloned at `~/GitRepositories/spirals/spirals/spirals.py`). Port query
  strings **verbatim** — do not hand-write or "improve" them.
- To add a use case: extract `{title, code, dialect, description, items:[{concept, jq_query}]}`
  from `spirals.py`, append to the embedded `<script id="spirals-data">` JSON in
  `completeness.html` **and** to `FAIR_spirals.json`, then add a color in `SPIRAL_COLORS`.
- **Validate every `jq_query` before embedding.** Run it under local `jq` (jq-1.6 is a good
  proxy for jq-web's stricter engine) against edge-case records (empty arrays, missing
  attributes, non-array/string values). Two known gotchas the lenient Python jq hides:
  1. Bare `count: if … end` fails to parse → wrap as `count: (if … end)`.
  2. Unguarded `has()` on a non-object throws and aborts the stream → lead with
     `(.x | type == "object") and (.x | has("…"))`.

## Scoring & UI model (completeness.html)

- Completeness per concept = admitted records / analyzed records (capped at 1).
- Use cases are grouped into four tabs: **FAIR** (feeds the headline Total), **Projects**,
  **SHARE** (five `SHARE_*` use cases built from existing items, sharescore.org framework),
  **Extras**. `TOTAL_CODES` defines which feed the repository Total. `weightedTotal(byCode,
  codes)` is the concept-count-weighted average; FAIR, Projects, and SHARE each show their
  own total, Extras shows none.
- DataCite API: send `&affiliation=true&publisher=true` (without them, publisher/affiliation
  concepts silently under-count). Optional `&resource-type-id=` and `&query=` filters.
  Random sampling fires multiple draws and dedups by DOI id; it falls back to deterministic
  most-recent fetch when the matching total ≤ Max.
- Reports: JSON (mirrors `FAIR_spirals.json` structure + run stats) and self-contained HTML
  (plots + tables, `page-break-inside:avoid` for clean PDF printing). Filenames:
  `{repository-id}_useCaseReport__{YYYY-MM-DDThh}.{json|html}`. Raw metadata downloads as
  `{repository-id}__{YYYYMMDDThh}.json`.

## Verifying changes

Behavior (jq init, DataCite fetch, scoring, plots) can't be checked by reading code alone —
**serve the page and exercise it** (the browser-preview MCP works well). After editing the
loader, fetch, queries, or scoring, re-run against `sjyq.oozvia` and confirm the numbers.

## Git / PRs

- Branch off `main` for changes; keep PRs scoped to one logical change.
- This environment has **no GitHub credentials** (no `gh`, HTTPS prompts fail, SSH keys not
  registered). Commit locally; the maintainer pushes and opens/merges PRs via GitHub Desktop.
  Provide the push command + a `compare/main...<branch>` URL and a suggested PR title/body.
- End commit messages with: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Don't commit `.claude/` or `.DS_Store`.
