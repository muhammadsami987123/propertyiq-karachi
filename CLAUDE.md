# CLAUDE.md — PropertyIQ (Project Context)

Context for AI coding assistants (Claude Code or similar) working in this repository. This is project-scoped and distinct from any global/user-level config. See `README.md` for full documentation and `AGENTS.md` for operational/agent instructions.

## What This Project Is

PropertyIQ is a Karachi, Pakistan real-estate intelligence platform. The product's core is an interactive map of Karachi backed by a researched market dataset — not a listings site, not a live-transaction feed.

## The Data-Honesty Principle (Critical)

This is the single most important rule in the codebase. **Never fabricate market figures, and never mark a research estimate as `verified` or present it as live/real-time data.**

- Every market record has a `data_type` (`verified`, `listing_aggregate`, `research_estimate`, `historical`, `calculated`, `user_provided`, `demo`) and a `confidence` (`high`, `medium`, `low`). These fields are load-bearing for user trust — do not default them to something more authoritative than the truth.
- If you are asked to add sample/placeholder data for development, it must be `data_type: "demo"` and must be visually/behaviorally distinguishable from real data in the UI. Never let demo data leak into a production-looking view unlabeled.
- If underlying data is insufficient for a trend, chart, or metric, the correct behavior is to say so explicitly ("Historical trend unavailable due to insufficient reliable observations") — not to interpolate or invent values to fill a gap.
- Every market figure should be traceable to a `source`/`source_url`, `collected_at`/`last_updated`, and (where relevant) `methodology`.

## File Ownership / Module Boundaries

| Path | Owns |
|---|---|
| `app/api/` | FastAPI route handlers only — no business logic |
| `app/models/` | Domain models + enums (`enums.py` is the single source of truth for vocabulary) |
| `app/schemas/` | Pydantic request/response schemas (the API contract) |
| `app/services/` | Business logic: market calculations, location lookups, search, analytics |
| `app/utils/` | Validation, calculations (yield, mortgage, etc.), PKR formatting |
| `app/data/` | Flat JSON/CSV/GeoJSON dataset — treat as the data layer, not scratch space |
| `frontend/templates/` | Server-rendered HTML (Jinja2) |
| `frontend/static/` | Tailwind CSS, vanilla JS, images — no build step, no frameworks |
| `tests/` | pytest suite, mirrors `app/` structure |
| `scripts/` | Standalone CLI tools (`import_data.py`, `validate_data.py`, `generate_market_summary.py`), stdlib-only, must run even before `requirements.txt` is installed |

Stay inside the module you were asked to touch. Don't reach into `app/data/` from `frontend/`, and don't put business logic in `app/api/`.

## Domain Vocabulary (canonical — `app/models/enums.py`)

- `property_type`: `house`, `apartment`, `plot`, `commercial`, `office`, `shop`
- `transaction_type`: `sale`, `rent`
- `market_category`: `premium`, `upper-mid`, `mid-market`, `affordable`, `emerging`, `commercial`, `mixed`
- `data_type`: `verified`, `listing_aggregate`, `research_estimate`, `historical`, `calculated`, `user_provided`, `demo`
- `confidence`: `high`, `medium`, `low`
- `currency`: always `"PKR"`

## Key Conventions

- **PKR formatting**: use `app/utils/formatting.py`'s Lakh/Crore-aware formatter for user-facing amounts (e.g. "PKR 2.5 Crore", "PKR 85 Lakh"); a raw numeric/standard toggle must remain available.
- **IDs/slugs**: kebab-case (`dha-phase-6`, `clifton`), stable once assigned — other records (`nearby_ids`, `location_id` foreign keys) depend on them.
- **Atomic writes**: any code that mutates `app/data/*.json` (admin endpoints, import scripts) must write to a temp file and `os.replace()` into place — never write the target file in place. See `scripts/import_data.py` for the reference pattern.
- **Referential integrity**: `location_id` fields (market records, trends, GeoJSON features) must reference an existing id in `karachi_locations.json`; `nearby_ids` must reference existing locations too. Run `python scripts/validate_data.py` after any dataset change.

## Where to Look for More

- `README.md` — architecture, API reference, dataset structure, setup/deployment.
- `AGENTS.md` — how to run/test the app, code style, agent-specific operating rules.
- `/methodology` (in-app page) — full confidence-scoring and sourcing methodology for end users.
