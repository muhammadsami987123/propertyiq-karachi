import pytest

from app.utils.formatting import format_pkr


@pytest.mark.parametrize(
    "amount,expected",
    [
        (25_000_000, "PKR 2.5 Crore"),
        (8_500_000, "PKR 85 Lakh"),
        (150_000, "PKR 1.5 Lakh"),
        (50_000, "PKR 50,000"),
        (0, "PKR 0"),
        (-2_000_000, "-PKR 20 Lakh"),
    ],
)
def test_format_pkr_pakistani_style(amount, expected):
    assert format_pkr(amount, "pakistani") == expected


def test_format_pkr_standard_style():
    assert format_pkr(25_000_000, "standard") == "PKR 25,000,000"
    assert format_pkr(8_500_000, "standard") == "PKR 8,500,000"


def test_format_pkr_unknown_style_raises():
    with pytest.raises(ValueError):
        format_pkr(1000, "bogus")
