from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_openapi_spec(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["title"] == "Construction Standard Price API"
    assert "/item" in spec["paths"]


def test_docs_page(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


def test_health(client: TestClient, require_database: None) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["message"] == "ok"


def test_ready_with_data(client: TestClient, require_database: None) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["quantity_items"] > 0
    assert body["data"]["market_prices"] > 0


def test_search_items(client: TestClient, require_database: None) -> None:
    response = client.get("/item", params={"cnstwk_div_cd": "A", "q": "가설", "size": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert len(body["data"]["items"]) > 0
    assert body["data"]["pagination"]["total"] > 0


def test_search_with_classification_filter(client: TestClient, require_database: None) -> None:
    response = client.get(
        "/item",
        params={"cnstwk_div_cd": "A", "lvl2_code": "AA", "size": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    for item in body["data"]["items"]:
        assert item["cnstwk_div_cd"] == "A"


def test_get_item_with_price(client: TestClient, require_database: None) -> None:
    response = client.get("/item/AAA162303500")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["price"] is not None
    assert float(body["data"]["price"]["expense_cost"]) > 0


def test_get_item_without_price(client: TestClient, require_database: None) -> None:
    response = client.get("/item/AAA161000000")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["price"] is None


def test_item_not_found_returns_failure_envelope(client: TestClient, require_database: None) -> None:
    response = client.get("/item/DOES_NOT_EXIST")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failure"
    assert "not found" in body["message"].lower()


def test_list_classification_roots(client: TestClient, require_database: None) -> None:
    response = client.get("/classification", params={"cnstwk_div_cd": "A"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert len(body["data"]["nodes"]) > 0


def test_list_work_divisions(client: TestClient, require_database: None) -> None:
    response = client.get("/work_division")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert len(body["data"]) == 6


def test_response_fields_are_snake_case(client: TestClient, require_database: None) -> None:
    response = client.get("/item", params={"size": 1})
    item = response.json()["data"]["items"][0]
    assert "qty_calc_ctycl_cd" in item
    assert "cnstwk_div_cd" in item
    assert "qtyCalcCtyclcd" not in item
