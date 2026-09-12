# PropertyIQ

**A visual intelligence layer for Karachi's real-estate market.**

PropertyIQ is a geospatial market-intelligence platform focused exclusively on Karachi, Pakistan. Instead of listing individual properties, it puts an interactive map of the city at the center of the experience and lets buyers, investors, landlords, agencies, and analysts explore sale and rental price ranges, price-per-square-foot, market trends, and investment metrics locality by locality.

PropertyIQ is built on a strict data-honesty principle: every market figure carries a `data_type` (verified, listing_aggregate, research_estimate, historical, calculated, user_provided, or demo) and a `confidence` level (high, medium, low), along with its source, collection date, and methodology where relevant. Research-derived estimates are always presented as estimates — "Research-based Estimate," "Observed Listing Range" — never as live transaction feeds or guaranteed figures. See [Disclaimer](#disclaimer) and the in-app `/methodology` page for the full policy.

## Architecture

PropertyIQ is a three-layer system:

- **Backend** — Python, FastAPI, Pydantic, Uvicorn. Serves a JSON REST API over the Karachi dataset and hosts the server-rendered frontend shell.
- **Frontend** — HTML, Tailwind CSS, vanilla JavaScript, and MapLibre GL JS. No frontend build step; templates and static assets are served directly by FastAPI.
- **Data layer** — flat JSON, CSV, and GeoJSON files under `app/data/`. No database in v1; the schema is deliberately shaped so it can migrate to PostgreSQL/PostGIS later without an application rewrite (see [Future Migration](#future-postgresqlpostgis-migration)).

```
Browser (MapLibre GL map + Tailwind UI)
        │  fetch() JSON
        ▼
FastAPI app (app/api/*)  ──►  services (app/services/*)  ──►  flat-file data (app/data/*)
        │
        ▼
 Jinja/HTML templates (frontend/templates)
```

## Installation

Requires Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

## Running Locally

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

## Project Structure

```
propertyiq/
├── app/
│   ├── main.py               # FastAPI app entrypoint
│   ├── config.py             # Settings (env-driven)
│   ├── api/                  # Route modules: locations, market, search, comparison, calculator, analytics, admin
│   ├── models/                # Domain models + enums (property_type, transaction_type, market_category, data_type, confidence)
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/               # Business logic (market, location, analytics, search)
│   ├── utils/                 # Validation, calculations, PKR formatting
│   └── data/
│       ├── locations/          # karachi_locations.json
│       ├── market/              # karachi_market_data.json, karachi_market_trends.json
│       ├── geo/                  # karachi_boundary.geojson, localities.geojson
│       └── sources/               # sources.json
├── frontend/
│   ├── templates/                  # Server-rendered HTML (Jinja2)
│   └── static/{css,js,assets}/     # Tailwind output, vanilla JS, images
├── tests/                            # pytest suite
├── scripts/
│   ├── import_data.py                 # CSV/JSON → dataset importer (upsert, atomic write)
│   ├── validate_data.py                # Dataset integrity checker
│   └── generate_market_summary.py       # Data-quality summary report
├── requirements.txt
├── .env.example
└── README.md
```

## Dataset Structure

All dataset files live under `app/data/` and are the authoritative contract every part of the app codes against.

| File | Shape | Purpose |
|---|---|---|
| `locations/karachi_locations.json` | array of `{id, slug, name, city, town, latitude, longitude, market_category, description, nearby_ids[]}` | Karachi locality registry |
| `geo/karachi_boundary.geojson` | GeoJSON Feature/FeatureCollection | Karachi's outer city boundary polygon |
| `geo/localities.geojson` | GeoJSON FeatureCollection | One Feature per location; `properties.location_id/name/market_category/has_boundary` |
| `market/karachi_market_data.json` | array of `{id, location_id, property_type, transaction_type, price_min, price_max, price_avg, price_per_sqft_min, price_per_sqft_max, currency, data_type, source, source_url, collected_at, last_updated, confidence, observations, methodology, notes}` | Sale/rent price records per locality × property type |
| `market/karachi_market_trends.json` | array of `{location_id, property_type, transaction_type, metric, period, value, data_type}` | Sparse historical series, only where sufficiently well-covered |
| `sources/sources.json` | array of `{id, name, url, type, description, terms_note}` | Source attribution registry |

**Domain vocabulary** (see `app/models/enums.py`):

- `property_type`: `house`, `apartment`, `plot`, `commercial`, `office`, `shop`
- `transaction_type`: `sale`, `rent`
- `market_category`: `premium`, `upper-mid`, `mid-market`, `affordable`, `emerging`, `commercial`, `mixed`
- `data_type`: `verified`, `listing_aggregate`, `research_estimate`, `historical`, `calculated`, `user_provided`, `demo`
- `confidence`: `high`, `medium`, `low`
- `currency`: always `"PKR"`

## Adding a New Karachi Location or Market Record

Two paths:

1. **Admin UI** (`/admin`, token-gated) — add/edit locations, add/update market records, import CSV/JSON/GeoJSON directly from the browser.
2. **CLI scripts**, for bulk or scripted updates:

```bash
# Import new market-data rows from CSV or JSON (upserts by id, or by
# location_id+property_type+transaction_type if id is omitted)
python scripts/import_data.py --file new_data.csv --type market

# Import new locations
python scripts/import_data.py --file new_locations.json --type locations

# Validate the full dataset before committing changes
python scripts/validate_data.py

# Generate a data-quality / coverage summary
python scripts/generate_market_summary.py --out summary.md
```

`import_data.py` validates every row against the schema, rejects rows that reference unknown `location_id`s (with a warning, not a hard failure), and writes atomically (temp file + `os.replace`) so a failed import never corrupts existing data. Always run `validate_data.py` after any manual edit to the dataset.

## Data-Source Methodology

Karachi's real-estate market has no centralized, publicly accessible transaction registry. PropertyIQ's dataset is therefore built from a combination of publicly available listing aggregates, public market reports, and manually researched estimates — never from unauthorized scraping. Every record declares its `data_type` and `source`/`source_url` so a reader can judge how much weight to give it.

**Confidence** (`high` / `medium` / `low`) is derived from:

- number of underlying observations
- source quality (public report vs. aggregated listings vs. estimate)
- data freshness (`last_updated` recency)
- geographic specificity (locality-level vs. town-level inference)
- consistency across independent sources

Full methodology, limitations, and per-record explanations are on the in-app **`/methodology`** page.

## Map Architecture

The map is built on **MapLibre GL JS** (open-source, no vendor lock-in) using **OpenFreeMap** free vector tiles as the base layer. Karachi's boundary and locality geometries are served from `app/data/geo/*.geojson` and rendered as GeoJSON overlays; localities without verified boundary data fall back to a point marker rather than a fabricated polygon. Data-driven layers (price, rent, price/sq-ft, growth, confidence) are expressed as MapLibre paint expressions keyed off each Feature's `location_id`, so switching the active metric only changes paint properties — no re-fetch of geometry.

## API Reference

Base URL: `http://localhost:8000`

| Method | Path | Description |
|---|---|---|
| GET | `/api/locations` | List all Karachi locations (summary fields) |
| GET | `/api/locations/{id}` | Location detail: overview, classification, nearby locations |
| GET | `/api/locations/{id}/market` | Sale + rent market records and trends for a location |
| GET | `/api/search` | Fuzzy search across location names/slugs |
| GET | `/api/comparison` | Side-by-side market comparison across two or more locations |
| POST | `/api/calculator` | Property investment calculator (yield, cash-on-cash, break-even, etc.) |
| GET | `/api/analytics/heatmap` | Geographic metric layer (price, rent, price/sq-ft, growth, confidence) |
| GET | `/api/geo/boundary` | Karachi outer boundary GeoJSON |
| GET | `/api/geo/localities` | Locality boundaries/points GeoJSON |
| GET/POST/PUT | `/api/admin/locations` | Token-gated: manage location records |
| GET/POST/PUT | `/api/admin/market` | Token-gated: manage market records |
| POST | `/api/admin/import/csv` | Token-gated: CSV import |
| POST | `/api/admin/import/geojson` | Token-gated: GeoJSON import |
| GET/POST | `/api/admin/sources` | Token-gated: manage source attribution |

Admin endpoints require a bearer token configured via environment variables — see `.env.example`.

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

Backend tests cover location lookup, search, market calculations, price formatting, rental-yield math, dataset validation, CSV/GeoJSON import, and API endpoints. Frontend interaction (search, map, filters, comparison, calculator) is covered separately under `tests/`.

## Future PostgreSQL/PostGIS Migration

The v1 flat-file schema was deliberately designed to map cleanly onto relational tables:

- `karachi_locations.json` → a `locations` table (lat/lon → a PostGIS `geometry(Point, 4326)` column)
- `karachi_market_data.json` → a `market_records` table, foreign-keyed on `location_id`
- `karachi_market_trends.json` → a `market_trends` table, same foreign key
- `*.geojson` → PostGIS `geometry(Polygon/MultiPolygon, 4326)` columns on `locations` / a `location_boundaries` table
- `sources.json` → a `sources` table, referenced by `market_records.source_id`

Enum fields (`property_type`, `transaction_type`, `market_category`, `data_type`, `confidence`) map directly to Postgres `ENUM` types or `CHECK` constraints. Because `app/services/*` already treats data access as its own layer, migrating storage means swapping the file-backed repository implementations for SQLAlchemy/PostGIS-backed ones — no change to `app/api/*` or the frontend contract.

## Deployment

PropertyIQ runs behind any ASGI-capable host (Uvicorn/Gunicorn+Uvicorn workers, Docker, most PaaS providers). Configuration is environment-variable driven — copy `.env.example` to `.env` and set values for your environment (admin token, host/port, CORS origins, etc.). No database provisioning is required for v1; ensure `app/data/` is writable if the admin UI's import/edit features will be used in production.

## Disclaimer

All market data in PropertyIQ is research-derived unless a record is explicitly marked `data_type: "verified"`. Price ranges, price-per-square-foot figures, trends, and investment metrics are estimates intended for general market orientation — they are **not** live transaction feeds, appraisals, or financial/investment advice. Confidence levels and methodology notes are provided so users can judge reliability for themselves. Always verify current pricing and terms directly with a licensed real-estate professional before making a financial decision.

---

Built by [Muhammad Sami](https://github.com/) (Muhammad Sami Asghar Mughal), COO at MARSA Empower.
