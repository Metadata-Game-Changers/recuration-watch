# Re-Curation Watch

A tool by [Metadata Game Changers](https://metadatagamechangers.com) for browsing any DataCite repository and inspecting the full revision history or activity of each DOI.

Live data is fetched directly from the [DataCite REST API](https://api.datacite.org) — no build step, no backend, no API key required. One HTML file, deploy anywhere.

## Features

- **Any DataCite repository** — enter any client ID (e.g. `sjyq.oozvia`, `cern.zenodo`) to load its full DOI collection
- **Activity history** per DOI — fetched on demand from `/dois/{id}/activities`, showing a chronological timeline of every create, update, and publish event
- **Before/after diff** for each change — field-level comparison showing what changed in each revision (URL, types, rights, related identifiers, dates, etc.)
- **Revision pulse bar** — color-coded bar chart across the activity history, building left (oldest/green) to right (newest)
- Filter by title, creator, or DOI string
- Filter by resource type and publication year
- Sort by last updated, publication year, or title
- URL-based state — repository, search query, type, and year filters are all reflected in the URL for bookmarking and sharing
- Live stats: total records, resource types, most recent year

## Deploy to GitHub Pages

1. Create or rename a repository to `recuration-watch`
2. Add `index.html` and `README.md` to the root of `main`
3. Go to **Settings → Pages → Source**: select `main` branch, `/ (root)`
4. Your site will be live at `https://[org].github.io/recuration-watch/`

Works on any static host (Netlify, Cloudflare Pages, etc.) — no build process required.

## URL parameters

| Parameter | Description | Example |
|---|---|---|
| `client` | DataCite client ID to load | `?client=sjyq.oozvia` |
| `q` | Search query | `&q=robinson` |
| `type` | Resource type filter | `&type=Dataset` |
| `year` | Publication year filter | `&year=2025` |

All parameters update automatically as you interact with the tool, making any view shareable via URL.

## API endpoints used

| Purpose | Endpoint |
|---|---|
| Client metadata | `GET /clients/{id}` |
| All DOIs for client | `GET /dois?client-id={id}&page[size]=100` |
| DOI activity log | `GET /dois/{id}/activities` |

Both DOI endpoints are public and CORS-enabled. The DataCite API paginates at 100 per page; the app fetches all pages automatically.

## Customization

- **Default repository**: change `DEFAULT_CLIENT` in the `<script>` block
- **Page size**: change `PAGE_SIZE` (default 15 records per page)
- **Colors**: all CSS custom properties are in the `:root` block

## Links

- [Metadata Game Changers](https://metadatagamechangers.com)
- [DataCite Commons](https://commons.datacite.org)
- [DataCite REST API docs](https://support.datacite.org/docs/api)
