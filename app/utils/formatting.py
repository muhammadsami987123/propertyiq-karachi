"""PKR currency formatting helpers (Pakistani Lakh/Crore style, or standard)."""

from __future__ import annotations

LAKH = 100_000
CRORE = 100_00_000  # 10,000,000


def format_pkr(amount: float, style: str = "pakistani") -> str:
    """Format a PKR amount.

    style="pakistani": below 1 Lakh -> "PKR <number>"; 1 Lakh+ -> "PKR X Lakh";
        1 Crore+ -> "PKR X Crore" (values rounded to at most 2 decimals, with
        trailing .0 trimmed).
    style="standard": "PKR 25,000,000" (comma-grouped, no decimals).
    """
    if style == "standard":
        return f"PKR {amount:,.0f}"

    if style != "pakistani":
        raise ValueError(f"Unknown formatting style: {style!r}")

    sign = "-" if amount < 0 else ""
    magnitude = abs(amount)

    if magnitude >= CRORE:
        value = magnitude / CRORE
        return f"{sign}PKR {_trim(value)} Crore"
    if magnitude >= LAKH:
        value = magnitude / LAKH
        return f"{sign}PKR {_trim(value)} Lakh"
    return f"{sign}PKR {magnitude:,.0f}"


def _trim(value: float) -> str:
    """Round to 2 decimals and strip trailing zeros / dangling dot."""
    rounded = round(value, 2)
    text = f"{rounded:.2f}".rstrip("0").rstrip(".")
    return text
