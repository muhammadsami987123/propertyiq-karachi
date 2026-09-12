import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_locations_returns_data():
    resp = client.get("/api/locations")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) > 0
    assert {"id", "name", "slug", "town", "latitude", "longitude", "market_category"} <= set(body[0].keys())


def test_get_known_location():
    resp = client.get("/api/locations/clifton")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "clifton"


def test_get_unknown_location_returns_clean_404():
    resp = client.get("/api/locations/not-a-real-place")
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body or "message" in body


def test_location_market_endpoint():
    resp = client.get("/api/locations/clifton/market")
    assert resp.status_code == 200
    body = resp.json()
    assert "sale" in body and "rent" in body
    assert "confidence_explanation" in body


def test_search_fuzzy_match():
    resp = client.get("/api/search", params={"q": "clifon"})
    assert resp.status_code == 200
    results = resp.json()
    assert any(r["id"] == "clifton" for r in results)


def test_search_empty_query_does_not_crash():
    resp = client.get("/api/search", params={"q": ""})
    assert resp.status_code == 200


def test_comparison_requires_at_least_two_ids():
    resp = client.get("/api/comparison", params={"ids": "clifton"})
    assert resp.status_code == 400


def test_comparison_valid_two_locations():
    resp = client.get("/api/comparison", params={"ids": "clifton,dha-phase-6"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["results"]) == 2
    assert body["not_found_ids"] == []


def test_comparison_reports_unknown_ids():
    resp = client.get("/api/comparison", params={"ids": "clifton,not-a-real-place"})
    assert resp.status_code == 200
    body = resp.json()
    assert "not-a-real-place" in body["not_found_ids"]


def test_calculator_basic_request():
    resp = client.post(
        "/api/calculator",
        json={
            "purchase_price": 20_000_000,
            "down_payment": 4_000_000,
            "interest_rate_pct": 15,
            "loan_term_years": 20,
            "monthly_rent": 90_000,
            "monthly_maintenance": 5_000,
            "annual_taxes_fees": 50_000,
            "vacancy_rate_pct": 5,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["monthly_payment"] > 0
    assert body["gross_yield_pct"] > 0


def test_calculator_rejects_down_payment_exceeding_price():
    resp = client.post(
        "/api/calculator",
        json={
            "purchase_price": 1_000_000,
            "down_payment": 2_000_000,
            "interest_rate_pct": 10,
            "loan_term_years": 10,
            "monthly_rent": 10_000,
            "monthly_maintenance": 1_000,
            "annual_taxes_fees": 5_000,
            "vacancy_rate_pct": 0,
        },
    )
    assert resp.status_code == 422


def test_heatmap_endpoint():
    resp = client.get(
        "/api/analytics/heatmap",
        params={"metric": "price_per_sqft", "transaction_type": "sale"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert len(body["items"]) > 0


def test_geo_boundary_is_valid_geojson():
    resp = client.get("/api/geo/boundary")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("type") in {"Feature", "FeatureCollection"}


def test_geo_localities_is_valid_geojson():
    resp = client.get("/api/geo/localities")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("type") == "FeatureCollection"
    assert len(body["features"]) > 0


def test_admin_endpoint_requires_token():
    resp = client.get("/api/admin/sources")
    assert resp.status_code == 401


def test_admin_endpoint_rejects_wrong_token():
    resp = client.get("/api/admin/sources", headers={"X-Admin-Token": "wrong-token"})
    assert resp.status_code == 401


@pytest.mark.parametrize(
    "path",
    ["/", "/explore", "/compare", "/investment", "/methodology", "/about", "/admin", "/karachi/clifton"],
)
def test_page_routes_render(path):
    resp = client.get(path)
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
