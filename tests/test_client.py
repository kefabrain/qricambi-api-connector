"""Tests for QRicambi API client using mocked HTTP responses."""

import pytest
import responses

from qricambi import QRicambiClient
from qricambi.exceptions import AuthenticationError, BadRequestError
from qricambi.models import (
    SearchResult,
    Supplier,
    VehicleInfo,
    OrderRow,
    ProductList,
    ProductListItem,
    EntityResult,
)

BASE = "https://api.qricambi.com"
TOKEN = "test-jwt-token"


@pytest.fixture
def client():
    return QRicambiClient(token=TOKEN)


# ── Supplier ─────────────────────────────────────────────────────────


@responses.activate
def test_list_suppliers(client):
    responses.add(
        responses.GET,
        f"{BASE}/mysupplier",
        json={
            "count": 2,
            "results": [
                {"name": "ACME", "loginUrl": "https://acme.com", "isEnable": True, "hasMoreThanTwoCredentials": False},
                {"name": "PARTS", "loginUrl": "https://parts.com", "isEnable": False, "hasMoreThanTwoCredentials": True},
            ],
        },
    )
    suppliers = client.list_suppliers()
    assert len(suppliers) == 2
    assert suppliers[0].name == "ACME"
    assert suppliers[0].is_enable is True
    assert suppliers[1].has_more_than_two_credentials is True


@responses.activate
def test_check_supplier(client):
    responses.add(
        responses.POST,
        f"{BASE}/checkmysupplier",
        json={"authenticated": True, "message": "", "supplier": "ACME"},
    )
    result = client.check_supplier("ACME", "user1", "pass1")
    assert result.authenticated is True
    assert result.supplier == "ACME"


# ── Entity extraction ────────────────────────────────────────────────


@responses.activate
def test_extract_entities(client):
    responses.add(
        responses.POST,
        f"{BASE}/entity/retrieves",
        json=[
            {"entity_type": "MARCA", "text": "Piaggio"},
            {"entity_type": "MODELLO", "text": "Porter"},
        ],
    )
    entities = client.extract_entities("filtro olio Piaggio Porter")
    assert len(entities) == 2
    assert entities[0].entity_type == "MARCA"
    assert entities[1].text == "Porter"


# ── Orders ───────────────────────────────────────────────────────────


@responses.activate
def test_list_orders(client):
    responses.add(
        responses.GET,
        f"{BASE}/orders/list",
        json=[
            {
                "id": 1,
                "accountID": 10,
                "qordernumber": "Q-001",
                "supplierordernumber": "S-001",
                "qty": 5,
                "note": "urgent",
                "statusid": 1,
                "create_at": "2026-01-01",
                "update_at": "",
                "confirm_at": "",
                "delete_at": "",
                "status": {"id": 1, "name": "new"},
            }
        ],
    )
    orders = client.list_orders(q_order_number="Q-001")
    assert len(orders) == 1
    assert orders[0].q_order_number == "Q-001"
    assert orders[0].qty == 5
    assert orders[0].status.name == "new"


@responses.activate
def test_add_order_row(client):
    responses.add(
        responses.POST,
        f"{BASE}/orders/row",
        json={
            "id": 99,
            "accountID": 10,
            "qordernumber": "Q-002",
            "supplierordernumber": "S-002",
            "qty": 3,
            "note": "",
            "statusid": 1,
            "create_at": "2026-04-27",
            "update_at": "",
            "confirm_at": "",
            "delete_at": "",
        },
    )
    row = client.add_order_row("Q-002", "S-002", qty=3)
    assert row.id == 99
    assert row.qty == 3


@responses.activate
def test_delete_order_rows(client):
    responses.add(responses.POST, f"{BASE}/orders/row/delete/bulk", body="ok")
    result = client.delete_order_rows([1, 2, 3])
    assert result == "ok"


# ── Product lists ────────────────────────────────────────────────────


@responses.activate
def test_create_product_list(client):
    responses.add(
        responses.POST,
        f"{BASE}/productlist",
        json={
            "id": "abc-123",
            "name": "Test List",
            "createdat": "2026-04-27",
            "updatedat": "2026-04-27",
            "active": True,
            "filename": "",
            "statusimport": "",
            "typeconf": "",
            "expiredate": "",
        },
    )
    pl = client.create_product_list("Test List")
    assert pl.id == "abc-123"
    assert pl.name == "Test List"
    assert pl.active is True


@responses.activate
def test_get_product_list_items(client):
    responses.add(
        responses.GET,
        f"{BASE}/productlist/abc-123/items",
        json={
            "rows": [
                {"code": "X1", "brand": "PIAGGIO", "price": 12.5, "qta": 10},
                {"code": "X2", "brand": "PIAGGIO", "price": 8.0, "qta": 5},
            ]
        },
    )
    items = client.get_product_list_items("abc-123")
    assert len(items) == 2
    assert items[0].code == "X1"
    assert items[0].price == 12.5


def test_add_items_over_limit(client):
    with pytest.raises(BadRequestError, match="1000"):
        client.add_product_list_items("abc", [{"code": f"C{i}", "brand": "B"} for i in range(1001)])


# ── Search ───────────────────────────────────────────────────────────


@responses.activate
def test_search_price_availability(client):
    responses.add(
        responses.POST,
        f"{BASE}/searchpriceandavailability",
        json=[
            {
                "Supplier": "ACME",
                "Code": "12345",
                "Description": "Oil filter",
                "Price": 15.50,
                "Matched": True,
                "Availability": {"Availability_code": 99, "Availability_desc": "Available"},
            }
        ],
    )
    results = client.search_price_availability(
        supplier="ACME", skus=["12345"], respect_rate_limit=False
    )
    assert len(results) == 1
    assert results[0].price == 15.50
    assert results[0].availability.is_available is True


def test_search_over_3_skus(client):
    with pytest.raises(BadRequestError, match="3 SKU"):
        client.search_price_availability("X", ["a", "b", "c", "d"], respect_rate_limit=False)


# ── Vehicle ──────────────────────────────────────────────────────────


@responses.activate
def test_vehicle_by_plate(client):
    responses.add(
        responses.GET,
        f"{BASE}/vehiclebyplate",
        json={
            "plate": "AB123CD",
            "vin": "ZFA12300000123456",
            "manufacturer": "PIAGGIO",
            "model": "PORTER",
            "enginecode": "HC",
            "hp": "48",
            "cc": "1300",
            "fuelsupply": "Diesel",
        },
    )
    v = client.vehicle_by_plate("ab 123 cd")
    assert v.plate == "AB123CD"
    assert v.manufacturer == "PIAGGIO"
    assert v.engine_code == "HC"


# ── Error handling ───────────────────────────────────────────────────


@responses.activate
def test_auth_error(client):
    responses.add(responses.GET, f"{BASE}/mysupplier", status=401, body="Unauthorized")
    with pytest.raises(AuthenticationError):
        client.list_suppliers()
