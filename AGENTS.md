# AGENTS.md

Instructions for autonomous coding agents (Claude Code, Copilot Workspace, etc.) operating in this repository.

## What This Is

PropertyIQ is a real, functioning product built by Muhammad Sami (MARSA Empower) — a Karachi real-estate intelligence platform, built as a genuine portfolio/product project. It is intended to work end-to-end, not as a mockup, demo shell, or UI-only prototype. Do not add placeholder buttons, fake API responses, "coming soon" states, or charts backed by invented numbers. If a feature can't be implemented reliably yet, leave it out rather than faking it.

## Running the App

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Serves at `http://localhost:8000`.

## Running Tests

```bash
pytest
```

## Validating Data Changes

**Any change to files under `app/data/` must pass validation before being committed:**

```bash
python scripts/validate_data.py
```

Exit code 0 = clean. This checks JSON/GeoJSON parse validity, required fields, enum values, numeric invariants (`price_min <= price_avg <= price_max`, non-negative prices, valid `price_per_sqft_min <= price_per_sqft_max`), ISO date strings, Karachi lat/lon bounds, and referential integrity (`location_id` foreign keys, `nearby_ids`, GeoJSON feature counts). It is stdlib-only and runs even without `requirements.txt` installed.

For bulk edits, prefer `python scripts/import_data.py --file <csv-or-json> --type {market|locations}` over hand-editing the JSON files — it validates and upserts atomically.

## Code Style

- **Python**: PEP 8, type-hinted (the codebase already uses `from __future__ import annotations` + modern `X | None` syntax — match it), Pydantic models for all API I/O shapes.
- **JavaScript (frontend)**: vanilla JS, no build step, no framework. Keep it dependency-light; MapLibre GL JS is the one significant external library.
- **HTML/CSS**: Tailwind CSS utility classes; avoid introducing a separate CSS framework.

## Module / File Ownership Boundaries

See `CLAUDE.md` for the full table. Summary: `app/api` (routes only), `app/models` (domain types/enums), `app/schemas` (API contracts), `app/services` (business logic), `app/utils` (validation/calculations/formatting), `app/data` (the dataset), `frontend/templates` + `frontend/static` (UI, no build step), `tests/` (pytest), `scripts/` (stdlib-only CLI tools). Stay inside the boundary of the module you're asked to change.

## The Data-Honesty Rule (Non-Negotiable)

Never fabricate market data. Never mislabel `data_type` or `confidence` to make data look more authoritative than it is — a `research_estimate` stays a `research_estimate`; it does not become `verified` because it would look better in the UI. Every market record needs source attribution (`source`/`source_url`), a `collected_at`/`last_updated` date, and a `confidence` level. Demo/seed data used for local development must be tagged `data_type: "demo"` and never presented as if it were real. If you're unsure whether a number is defensible, don't invent one — surface "data unavailable" instead.

## More Detail

- `README.md` — architecture, dataset structure, API reference, deployment.
- `CLAUDE.md` — condensed project context, domain vocabulary, conventions.
- `/methodology` (in-app) — confidence scoring and sourcing methodology.
