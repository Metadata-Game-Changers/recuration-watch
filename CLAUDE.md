# CLAUDE.md

Guidance for working in this repository.

## What this is

Static, single-file web apps for Metadata Game Changers, deployed via GitHub Pages
(deploy from a branch — `main` / root; no build step, no Actions). Each app is one
self-contained HTML file with inline CSS + vanilla JS — no framework, no bundler.

- `index.html` — **Re-Curation Watch** (the original tool).
- `completeness.html` — **Metadata Completeness**: scores a DataCite repository against
  MGC FAIR/DataCite/Project use cases. Runs MGC's `jq` queries **in the browser** via
  jq-web (jq compiled to WASM) and fetches live DOIs from `api.datacite.org`.
- `repo-activity.html` — repository activity view.
- `FAIR_spirals.json` — readable catalog of the use cases (also **embedded** inside
  `completeness.html`; keep the two in sync).
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
- Use cases are grouped into three tabs: **FAIR** (feeds the headline Total), **Projects**,
  **Extras**. `TOTAL_CODES` defines which feed the repository Total. `weightedTotal(byCode,
  codes)` is the concept-count-weighted average; FAIR and Projects each show their own total,
  Extras shows none.
- DataCite API: send `&affiliation=true&publisher=true` (without them, publisher/affiliation
  concepts silently under-count). Optional `&resource-type-id=` and `&query=` filters.
  Random sampling fires multiple draws and dedups by DOI id; it falls back to deterministic
  most-recent fetch when the matching total ≤ Max.
- Reports: JSON (mirrors `FAIR_spirals.json` structure + run stats) and self-contained HTML
  (plots + tables, `page-break-inside:avoid` for clean PDF printing). Filenames:
  `{repository-id}_useCaseReport__{YYYY-MM-DD_HH}.{json|html}`.

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
