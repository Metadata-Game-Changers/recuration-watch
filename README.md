# Re-Curation Watch — and the Metadata Game Changers DataCite tools

*Found a bug or have feedback? Please [open a GitHub issue](https://github.com/Metadata-Game-Changers/recuration-watch/issues/new/choose).*

[![DOI](https://img.shields.io/badge/DOI-10.60872%2FrecurationWatch-blue)](https://doi.org/10.60872/recurationWatch)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey)](https://creativecommons.org/licenses/by-nc/4.0/)

A suite of browser-based tools by [Metadata Game Changers](https://metadatagamechangers.com) for exploring and improving DataCite metadata — its **provenance**, **completeness**, **connectivity**, and **curation activity**.

Everything runs in your browser against the live [DataCite REST API](https://api.datacite.org): no build step, no backend, no API key, nothing uploaded or stored. Each tool is one self-contained HTML file, so the whole suite deploys to any static host.

Start at **[tools.html](tools.html)** for a one-page overview, or jump straight to a tool below.

## The tools

| Tool | File | What it does | DOI |
|---|---|---|---|
| **Re-Curation Watch** | [`index.html`](index.html) | Browse a repository's DOIs and inspect each DOI's full **curation history** — who changed what, when — with before/after field diffs and a per-section change timeline. | [10.60872/recurationWatch](https://doi.org/10.60872/recurationWatch) |
| **Metadata Completeness** | [`completeness.html`](completeness.html) | Score a repository (or a single DOI) against the MGC **FAIR**, **DataCite**, and **Project** use cases, and drill into any concept's values. Runs the methodology's `jq` queries in the browser via [jq-web](https://github.com/fiatjaf/jq-web). | [10.60872/metadataCompleteness](https://doi.org/10.60872/metadataCompleteness) |
| **Metadata Connectivity** | [`metadataConnectivity.html`](metadataConnectivity.html) | Measure **identifier connectivity** — how many creators, contributors, funders, publishers, and rights carry the identifiers (ORCID, ROR, …) that connect them — with drill-downs to the exact records and hand-offs to the retrievers. | [10.60872/metadataConnectivity](https://doi.org/10.60872/metadataConnectivity) |
| **Repository Activity** | [`repo-activity.html`](repo-activity.html) | Plot a repository's **curation activity over time**, broken down by changed property and by the actor who made the change. | [10.60872/repositoryActivity](https://doi.org/10.60872/repositoryActivity) |
| **Repository History** | [`repositoryHistory.html`](repositoryHistory.html) | Score completeness for **every registered year** and plot the use-case trends over time (a cohort view — records as they are today). | [10.60872/repositoryHistory](https://doi.org/10.60872/repositoryHistory) |
| **ROR Retriever** | [`rorRetriever.html`](rorRetriever.html) | Match **affiliation strings to ROR identifiers** (a browser port of [RORRetriever](https://github.com/Metadata-Game-Changers/RORRetriever)). | [10.60872/rorRetriever](https://doi.org/10.60872/rorRetriever) |
| **ORCID Retriever** | [`orcidRetriever.html`](orcidRetriever.html) | Find **ORCID iDs for people** by name, with employment and journal context for disambiguation (a browser port of the name→ORCID flow in [ORCID-Tools](https://github.com/Metadata-Game-Changers/ORCID-Tools)). | [10.60872/orcidRetriever](https://doi.org/10.60872/orcidRetriever) |

Supporting pages: **[useCases.html](useCases.html)** (the completeness use-case catalog), **[connectivityAbout.html](connectivityAbout.html)** and **[rorAbout.html](rorAbout.html)** (background), and **[tips.html](tips.html)** (the collected while-you-wait tips).

## How the tools work together

- **Live data, nothing stored.** Every tool fetches directly from `api.datacite.org`. No account, no upload, no server.
- **Repository, prefix, or a single DOI.** Enter a repository name / client ID, a DOI prefix, or a single DOI. Completeness and Connectivity analyze one DOI as easily as a whole repository.
- **Shared selection.** The current repository (and DOI or filters) travels between tools through the top-bar links and URL parameters — `?client=`, `?doi=`, `?resource-type=`, `?query=` — so you can pivot from completeness to connectivity to history on the same selection without retyping it.
- **Exact-sample sharing.** *Share with Metadata Connectivity / Completeness* hands the **exact sampled records** from one tool to the other (and Repository History can open any year's sample in either), so both measure the identical set instead of drawing a fresh random sample. Small samples travel through `localStorage`; large ones (many thousands of records) through IndexedDB.
- **Actionable drill-downs.** Connectivity's drill-downs link the **Occurrences / Identified / To-fix** counts to the specific DOIs, and send the names still missing identifiers straight to the ROR and ORCID retrievers.
- **Exports everywhere.** JSON / HTML / PDF / CSV reports, plus PNG charts and timelines you can save or copy to the clipboard.
- **Bookmarkable URLs.** Every view encodes its state in the URL, so any result is shareable.

---

## Re-Curation Watch in detail

Re-Curation Watch surfaces the metadata provenance DataCite records for every DOI since March 2019. For each update event you can see exactly which fields changed, with before and after values side by side — so you can assess not just what a repository's metadata says now, but how it got there.

*Re-Curation Watch queries the public DataCite REST API, which is freely accessible without authentication. DOI metadata is provided by DataCite member repositories and carries the licenses those repositories assign.*

### Finding a repository, prefix, or DOI

Type into the search box in the purple hero bar:

- a **repository name** (e.g. "Zenodo", "Dryad", "Gump Station") or **client ID** (e.g. `cern.zenodo`, `sjyq.oozvia`) — an autocomplete dropdown shows matches with their DOI counts;
- a **prefix** (e.g. `10.18739`) — loads the most recently updated records for that prefix;
- a **single DOI** (e.g. `10.60872/recurationWatch`) — loads that one DOI's curation history.

Press Enter or click **Explore →**. The tool loads with the Metadata Game Changers repository by default.

### Filters

All filters are in the toolbar below the hero and work together — applying one updates the options available in the others.

- **Search** — free-text across titles, creator names, and DOI strings.
- **Type** — DataCite resource type (Dataset, Software, Text, …); options reflect what exists in the current set.
- **Updated** — the year the record was last modified in DataCite (most recent curation activity, which may differ from the publication year).
- **Min. versions** — DOIs with at least a given `metadataVersion`. DataCite increments this counter on every system change (including automated ones), so it is a proxy for curation activity; the dropdown shows only values that exist in the current set.
- **Re-curated only** — DOIs whose `updated` timestamp is more than a day after `created` — records with genuine post-registration curation, not just the original creation event.
- **Reset** — clears all filters and resets sort to Updated.

> `metadataVersion` can exceed the number of activity-log entries, since not every system change generates a provenance record. Open a DOI's history panel to see the exact count of recorded events.

### Sorting

**Updated** (most recently modified first, the default), **Published** (`publicationYear`), and **Title** (alphabetical).

### Viewing curation history

Click **history** on any DOI card to load its activity timeline. Each event shows the date, action type (create / update / publish, color-coded), a one-line summary ("Updated rights / licenses, related identifiers."), and a **Show details ▸** toggle that expands the full before/after field diff.

Above the table, a **section change timeline** shows one bar per major metadata section (Titles, Creators, Rights, …) across the DOI's life: each bar keeps its colour until that section changed, then the hue shifts — and stays solid for sections that never changed. Cells are spaced along a real time axis (toggle to equal-per-event), and the whole timeline can be **saved or copied as a PNG**.

### URL state

Every filter choice, sort order, and page is reflected in the URL, so any view is bookmarkable and shareable:

| Parameter | Description | Example |
|---|---|---|
| `client` | DataCite client ID | `?client=sjyq.oozvia` |
| `doi` | A single DOI | `?doi=10.60872/recurationWatch` |
| `q` | Search query | `&q=robinson` |
| `type` | Resource type | `&type=Dataset` |
| `year` | Updated year | `&year=2024` |
| `version` | Min. metadata version | `&version=3` |
| `recur` | Re-curated only | `&recur=1` |
| `sort` | Sort order | `&sort=title` |

---

## Deploy to GitHub Pages

This repository is served with GitHub Pages straight from a branch — no build step, no Actions.

1. Put the tool files (the `.html` files, `FAIR_spirals.json`, the favicon, `LICENSE`, `README.md`) in the root of `main`.
2. **Settings → Pages → Source**: select the `main` branch, `/ (root)`.
3. The suite is live at `https://[org].github.io/recuration-watch/` — e.g. [`tools.html`](tools.html) for the overview or [`index.html`](index.html) for Re-Curation Watch.

Any static host works (Netlify, Cloudflare Pages, …).

## API endpoints used

| Purpose | Endpoint |
|---|---|
| Repository search / metadata | `GET /clients?query={name}` · `GET /clients/{id}` |
| DOIs for a repository | `GET /dois?client-id={id}&affiliation=true&publisher=true` |
| A single DOI | `GET /dois/{doi}?affiliation=true&publisher=true` |
| DOI activity (provenance) log | `GET /dois/{doi}/activities` |

All endpoints are public and CORS-enabled. `affiliation=true&publisher=true` returns affiliation and publisher as structured objects (needed for completeness and connectivity). Completeness and Connectivity support random sampling with multiple draws, de-duplicated by DOI, for large repositories.

## Development notes

- **No build.** Each tool is a single self-contained HTML file with inline CSS and vanilla JS.
- **Completeness engine.** `completeness.html` runs MGC's `jq` use-case queries in the browser via jq-web (jq compiled to WASM); the use-case catalog lives in `FAIR_spirals.json` (and embedded in the page). `repositoryHistory.html` reuses the same scoring per year.
- **Generated pages.** `tips.html` is generated from each tool's tips array by `makeTipsPage.py` — edit the tips in the tool, then regenerate.

## Citation

Each tool has its own DOI (see the table above) — please cite the one you used. For the suite / Re-Curation Watch:

> Robinson, E. and Habermann, T. (2026). *Re-Curation Watch* (v1.0). Metadata Game Changers LLC. https://doi.org/10.60872/recurationWatch

## Links

- [Metadata Game Changers](https://metadatagamechangers.com)
- [DataCite Commons](https://commons.datacite.org)
- [DataCite REST API docs](https://support.datacite.org/docs/api)
- [DataCite provenance documentation](https://support.datacite.org/docs/tracking-provenance)
