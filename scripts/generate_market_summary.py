#!/usr/bin/env python3
"""
generate_market_summary.py — Human-readable data-quality summary for
PropertyIQ's Karachi dataset.

Reads app/data/locations/karachi_locations.json and
app/data/market/karachi_market_data.json and prints a Markdown report
covering coverage, breakdowns, confidence distribution, and data-coverage
gaps (locations with zero market records).

Usage:
    python scripts/generate_market_summary.py
    python scripts/generate_market_summary.py --out summary.md
    python scripts/generate_market_summary.py --data-dir app/data

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def load_json_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def build_summary(locations: list[dict], market_records: list[dict]) -> str:
    lines: list[str] = []

    lines.append("# PropertyIQ — Karachi Dataset Summary")
    lines.append("")

    total_locations = len(locations)
    total_market_records = len(market_records)
    lines.append(f"- **Total locations covered:** {total_locations}")
    lines.append(f"- **Total market records:** {total_market_records}")
    lines.append("")

    if total_locations == 0:
        lines.append("No location data found yet — nothing further to summarize.")
        return "\n".join(lines)

    # Breakdown by market_category
    category_counts = Counter(loc.get("market_category", "unspecified") for loc in locations)
    lines.append("## By Market Category")
    lines.append("")
    lines.append("| Category | Locations |")
    lines.append("|---|---:|")
    for category, count in sorted(category_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {category} | {count} |")
    lines.append("")

    # Breakdown by town
    town_counts = Counter(loc.get("town") or "unspecified" for loc in locations)
    lines.append("## By Town")
    lines.append("")
    lines.append("| Town | Locations |")
    lines.append("|---|---:|")
    for town, count in sorted(town_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {town} | {count} |")
    lines.append("")

    # Market records by property_type / transaction_type
    lines.append("## Market Records by Property Type & Transaction Type")
    lines.append("")
    pt_tt_counts = Counter(
        (rec.get("property_type", "unspecified"), rec.get("transaction_type", "unspecified"))
        for rec in market_records
    )
    lines.append("| Property Type | Transaction Type | Records |")
    lines.append("|---|---|---:|")
    for (pt, tt), count in sorted(pt_tt_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {pt} | {tt} | {count} |")
    lines.append("")

    # Confidence distribution
    confidence_counts = Counter(rec.get("confidence", "unspecified") for rec in market_records)
    lines.append("## Confidence Distribution")
    lines.append("")
    lines.append("| Confidence | Records | Share |")
    lines.append("|---|---:|---:|")
    for level in ("high", "medium", "low"):
        count = confidence_counts.get(level, 0)
        share = f"{(count / total_market_records * 100):.1f}%" if total_market_records else "0.0%"
        lines.append(f"| {level} | {count} | {share} |")
    other = sum(v for k, v in confidence_counts.items() if k not in ("high", "medium", "low"))
    if other:
        lines.append(f"| unspecified/other | {other} | — |")
    lines.append("")

    # Data type distribution (bonus, useful for the honesty principle)
    data_type_counts = Counter(rec.get("data_type", "unspecified") for rec in market_records)
    lines.append("## Data Type Distribution")
    lines.append("")
    lines.append("| Data Type | Records |")
    lines.append("|---|---:|")
    for dtype, count in sorted(data_type_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {dtype} | {count} |")
    lines.append("")

    # Coverage gaps: locations with zero market records
    covered_location_ids = {rec.get("location_id") for rec in market_records if rec.get("location_id")}
    gap_locations = [loc for loc in locations if loc.get("id") not in covered_location_ids]

    lines.append("## Data Coverage Gaps")
    lines.append("")
    if not gap_locations:
        lines.append("None — every location has at least one market record.")
    else:
        lines.append(f"{len(gap_locations)} location(s) have zero market records:")
        lines.append("")
        for loc in gap_locations:
            name = loc.get("name", loc.get("id", "unknown"))
            town = loc.get("town", "unspecified")
            lines.append(f"- {name} (town: {town}, id: {loc.get('id')})")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Karachi dataset market summary.")
    parser.add_argument(
        "--data-dir",
        default="app/data",
        help="Path to the app/data directory (default: app/data)",
    )
    parser.add_argument("--out", help="Optional file path to also write the summary to")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    locations = load_json_list(data_dir / "locations" / "karachi_locations.json")
    market_records = load_json_list(data_dir / "market" / "karachi_market_data.json")

    summary = build_summary(locations, market_records)
    print(summary)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(summary + "\n", encoding="utf-8")
        print(f"\n(Also written to {out_path})", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
