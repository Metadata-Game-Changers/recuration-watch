# If you have feedback or find a bug please let us know through [Github issues](https://github.com/Metadata-Game-Changers/recuration-watch/issues/new/choose)! 
# Re-Curation Watch
[![DOI](https://img.shields.io/badge/DOI-10.60872%2FrecurationWatch-blue)](https://doi.org/10.60872/recurationWatch)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey)](https://creativecommons.org/licenses/by-nc/4.0/)

A tool by [Metadata Game Changers](https://metadatagamechangers.com) for browsing any DataCite repository and inspecting the full curation history of each DOI — who changed what, when, and how.

Live data is fetched directly from the [DataCite REST API](https://api.datacite.org) — no build step, no backend, no API key required. One HTML file, deploy anywhere. 

## What it does 

Re-Curation Watch surfaces the metadata provenance that DataCite records for every DOI since March 2019. For each update event you can see exactly which fields changed, with before and after values shown side by side. This makes it possible to assess the curation quality of any DataCite repository — not just what the metadata says now, but how it got there.

Note: Re-Curation Watch queries the DataCite Public REST API, which is freely accessible without authentication. DOI metadata displayed is provided by DataCite member repositories and carries the licenses assigned by those repositories. DataCite's own documentation is licensed CC-BY 4.0.


## Finding a repository, DOI, or prefix

Type a repository name (e.g. "Zenodo", "Dryad", "Gump Station") or a DataCite client ID (e.g. `cern.zenodo`, `sjyq.oozvia`) into the search box in the purple hero bar. An autocomplete dropdown shows matching repositories with their DOI counts. Press Enter or click **Explore →** to load.

Type a prefix in and the most recently updated 2000 records for a specific prefix will load.

Type in a specific DOI and the history for that DOI will load. 

The tool loads with the Metadata Game Changers repository by default.

## Filters

All filters are in the toolbar below the hero. They work together — applying one filter updates the available options in the others.

**Search** — free-text search across titles, creator names, and DOI strings.

**Type** — filter by DataCite resource type (Dataset, Software, Text, etc.). Options shown reflect what exists in the current filtered set.

**Updated** — filter by the year the DOI record was last modified in DataCite. This is the year of the most recent curation activity, which may differ from the publication year.

**Min. versions** — filter to DOIs with a minimum `metadataVersion` value. DataCite increments this counter each time a DOI record is touched in their system, including automated changes, so it is a proxy for curation activity rather than an exact count of deliberate updates. The dropdown shows only the distinct version values that actually exist in the currently filtered set, with a count of how many DOIs have at least that many versions — so options reduce as you apply other filters and you can never select a value with zero results.

Note: `metadataVersion` can be higher than the number of entries in the activity log, since not all system changes generate a provenance record. Open the history panel on any DOI to see the exact count of recorded activity events.

**Re-curated only** — checkbox that filters to DOIs where the `updated` timestamp is more than one day later than the `created` timestamp. This identifies records that received genuine post-registration curation, as opposed to DOIs where the only activity is the original creation event. Useful for finding evidence of active metadata maintenance in a repository.

**Reset** — clears all filters and resets sort to Updated.

## Sorting

Three sort options in the toolbar: **Updated** (most recently modified first), **Published** (by `publicationYear`), and **Title** (alphabetical). Default is Updated, which surfaces the most recently curated records first.

## Viewing curation history

Click the **history** button on any DOI card to load its activity timeline. Each event shows:

- Date and action type (create, update, publish) with color coding
- A one-line summary of what changed ("Updated rights / licenses, related identifiers.")
- **Show details ▸** — expands the full before/after field diff for that event

At the top of the history panel, a **revision pulse bar** shows the full activity sequence left to right: the leftmost (shortest, green) bar is the creation event, and bars grow taller moving right toward the most recent activity. Color indicates action type: green = create, blue = update, amber = publish.

## URL state

Every filter choice, sort order, and page is reflected in the URL automatically, making any view bookmarkable and shareable:

| Parameter | Description | Example |
|---|---|---|
| `client` | DataCite client ID | `?client=sjyq.oozvia` |
| `q` | Search query | `&q=robinson` |
| `type` | Resource type | `&type=Dataset` |
| `year` | Updated year | `&year=2024` |
| `version` | Min. metadata version | `&version=3` |
| `recur` | Re-curated only | `&recur=1` |
| `sort` | Sort order | `&sort=title` |

## Deploy to GitHub Pages

1. Create or rename a repository to `recuration-watch`
2. Add `index.html`, `README.md`, `LICENSE`, and `favicon_MGC.png` to the root of `main`
3. Go to **Settings → Pages → Source**: select `main` branch, `/ (root)`
4. Your site will be live at `https://[org].github.io/recuration-watch/`

Works on any static host (Netlify, Cloudflare Pages, etc.) — no build process required.

## API endpoints used

| Purpose | Endpoint |
|---|---|
| Repository search | `GET /clients?query={name}` |
| Repository metadata | `GET /clients/{id}` |
| All DOIs for repository | `GET /dois?client-id={id}&page[size]=100` |
| DOI activity log | `GET /dois/{id}/activities` |

All endpoints are public and CORS-enabled. The DOI endpoint paginates at 100 per page; the app fetches all pages automatically (capped at 2,000 records for performance).

## Customization

- **Default repository**: change `DEFAULT_CLIENT` in the `<script>` block
- **Page size**: change `PAGE_SIZE` (default 50 records per page)
- **Colors**: all CSS custom properties are in the `:root` block; the purple hero uses `#9167b0`

## Citation

If you use Re-Curation Watch in your work, please cite it as:

Robinson, E. and Habermann, T. (2026). Re-Curation Watch (v1.0). Metadata Game Changers LLC. https://doi.org/10.60872/recurationWatch

## Links

- [Metadata Game Changers](https://metadatagamechangers.com)
- [DataCite Commons](https://commons.datacite.org)
- [DataCite REST API docs](https://support.datacite.org/docs/api)
- [DataCite provenance documentation](https://support.datacite.org/docs/tracking-provenance)
