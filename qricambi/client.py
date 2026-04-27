"""QRicambi API client — full connector for api.qricambi.com"""

from __future__ import annotations

import os
import time
from typing import Any, Optional

import requests

from .exceptions import (
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    QRicambiError,
    RateLimitError,
    ServerError,
)
from .models import (
    CheckSupplierResult,
    EntityResult,
    OrderRow,
    ProductList,
    ProductListItem,
    SearchResult,
    Supplier,
    VehicleInfo,
)

BASE_URL = "https://api.qricambi.com"
AUTH_URL = "https://app.qricambi.com/api"
SEARCH_MIN_INTERVAL = 30  # seconds between search requests


class QRicambiClient:
    """Python client for the QRicambi API.

    Create with a token directly, or use the ``login()`` class method
    to authenticate with username/password.

    Args:
        token: Bearer JWT token for authentication.
        base_url: API base URL (default: https://api.qricambi.com).
        timeout: Request timeout in seconds (default: 30).
    """

    def __init__(
        self,
        token: str,
        base_url: str = BASE_URL,
        timeout: int = 30,
    ):
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        self._last_search_time: float = 0.0
        self._token_expires: str = ""
        self._remember_key: str = ""

    # ── Authentication ───────────────────────────────────────────────

    @classmethod
    def login(
        cls,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_url: str = BASE_URL,
        timeout: int = 30,
    ) -> "QRicambiClient":
        """Authenticate with username/password and return a ready client.

        Credentials can be passed directly or via environment variables:
          - QRICAMBI_USERNAME
          - QRICAMBI_PASSWORD

        Args:
            username: QRicambi account email.
            password: QRicambi account password.
        """
        username = username or os.environ.get("QRICAMBI_USERNAME", "")
        password = password or os.environ.get("QRICAMBI_PASSWORD", "")
        if not username or not password:
            raise AuthenticationError(
                "Username and password required. Pass them directly or set "
                "QRICAMBI_USERNAME / QRICAMBI_PASSWORD environment variables.",
                status_code=None,
            )
        resp = requests.post(
            f"{AUTH_URL}/User/RequestToken",
            json={
                "username": username.strip(),
                "password": password.strip(),
                "rememberMe": "true",
            },
            timeout=timeout,
        )
        if not resp.ok:
            raise AuthenticationError(
                f"Login failed ({resp.status_code}): {resp.text}",
                status_code=resp.status_code,
            )
        data = resp.json()
        token = data.get("token", "")
        if not token:
            raise AuthenticationError("Login response missing token", status_code=None)
        client = cls(token=token, base_url=base_url, timeout=timeout)
        client._token_expires = data.get("expires", "")
        client._remember_key = data.get("rememberKey", "")
        return client

    @classmethod
    def from_env(cls, base_url: str = BASE_URL, timeout: int = 30) -> "QRicambiClient":
        """Create client from QRICAMBI_TOKEN env var, or login via env credentials."""
        token = os.environ.get("QRICAMBI_TOKEN", "")
        if token:
            return cls(token=token, base_url=base_url, timeout=timeout)
        return cls.login(base_url=base_url, timeout=timeout)

    @property
    def token_expires(self) -> str:
        """ISO timestamp when the current token expires."""
        return self._token_expires

    # ── HTTP helpers ─────────────────────────────────────────────────

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self._timeout)
        url = f"{self._base_url}{path}"
        resp = self._session.request(method, url, **kwargs)
        self._raise_for_status(resp)
        return resp

    @staticmethod
    def _raise_for_status(resp: requests.Response) -> None:
        if resp.ok:
            return
        msg = resp.text or resp.reason
        status = resp.status_code
        error_map = {
            400: BadRequestError,
            401: AuthenticationError,
            403: ForbiddenError,
            404: NotFoundError,
            429: RateLimitError,
            500: ServerError,
        }
        exc_cls = error_map.get(status, QRicambiError)
        raise exc_cls(msg, status_code=status)

    # ── Supplier ─────────────────────────────────────────────────────

    def list_suppliers(self) -> list[Supplier]:
        """Retrieve list of all suppliers used in your account."""
        resp = self._request("GET", "/mysupplier")
        data = resp.json()
        return [Supplier.from_dict(s) for s in data.get("results", [])]

    def check_supplier(
        self, supplier: str, user: str, password: str
    ) -> CheckSupplierResult:
        """Validate credentials for a supplier's system.

        New suppliers are automatically added to your supplier list.
        For suppliers with extra credentials, format user as "username;extra".
        """
        resp = self._request(
            "POST",
            "/checkmysupplier",
            json={"supplier": supplier, "user": user, "password": password},
        )
        data = resp.json()
        if isinstance(data, list) and data:
            return CheckSupplierResult.from_dict(data[0])
        return CheckSupplierResult.from_dict(data)

    # ── Entity extraction ────────────────────────────────────────────

    def extract_entities(self, text: str) -> list[dict]:
        """Extract entities from text using QRicambi NLP.

        Returns parsed Quote objects with car info and quote items.
        Input recognized: MARCA, MODELLO, ALLESTIMENTO, DATA,
        COD_MOTORE, TARGA, TELAIO, POTENZA, CILINDRATA, CODICE,
        DESCRIZIONE, DETTAGLIO, CONDIZIONE, MARCA_PROD, QUANTITA.
        """
        import json as _json
        resp = self._request(
            "POST", "/entity/retrieves", json={"content": text}
        )
        data = resp.json()
        # API returns a JSON string wrapping a list of Quote objects
        if isinstance(data, str):
            try:
                data = _json.loads(data)
            except _json.JSONDecodeError:
                return [{"raw": data}]
        if isinstance(data, list):
            return data
        return [data]

    # ── Orders ───────────────────────────────────────────────────────

    def list_orders(
        self, q_order_number: str = "", supplier_order_number: str = ""
    ) -> list[OrderRow]:
        """Retrieve order rows, optionally filtered by order numbers."""
        params: dict[str, str] = {}
        if q_order_number:
            params["qordernumber"] = q_order_number
        if supplier_order_number:
            params["supplierordernumber"] = supplier_order_number
        resp = self._request("GET", "/orders/list", params=params)
        data = resp.json()
        if isinstance(data, list):
            return [OrderRow.from_dict(r) for r in data]
        return [OrderRow.from_dict(data)] if data else []

    def add_order_row(
        self,
        q_order_number: str,
        supplier_order_number: str,
        qty: int,
        note: str = "",
        customer_id: int | None = None,
        from_search_row: dict | None = None,
    ) -> OrderRow:
        """Add a new order row."""
        body: dict[str, Any] = {
            "qordernumber": q_order_number,
            "supplierordernumber": supplier_order_number,
            "qty": qty,
            "note": note,
        }
        if customer_id is not None:
            body["customerid"] = {"int64": customer_id, "valid": True}
        if from_search_row:
            body["fromsearchrow"] = from_search_row
        resp = self._request("POST", "/orders/row", json=body)
        return OrderRow.from_dict(resp.json())

    def update_order_row(
        self,
        row_id: int,
        q_order_number: str | None = None,
        supplier_order_number: str | None = None,
        qty: int | None = None,
        note: str | None = None,
        customer_id: int | None = None,
        from_search_row: dict | None = None,
    ) -> dict:
        """Update an existing order row."""
        body: dict[str, Any] = {"id": row_id}
        if q_order_number is not None:
            body["qordernumber"] = q_order_number
        if supplier_order_number is not None:
            body["supplierordernumber"] = supplier_order_number
        if qty is not None:
            body["qty"] = str(qty)
        if note is not None:
            body["note"] = note
        if customer_id is not None:
            body["customerid"] = str(customer_id)
        if from_search_row is not None:
            body["fromsearchrow"] = from_search_row
        resp = self._request("PUT", "/orders/row", json=body)
        return resp.json()

    def delete_order_rows(self, row_ids: list[int]) -> str:
        """Bulk delete order rows by IDs."""
        resp = self._request("POST", "/orders/row/delete/bulk", json=row_ids)
        return resp.text

    def undo_delete_order_rows(self, row_ids: list[int]) -> str:
        """Undo bulk deletion of order rows."""
        resp = self._request("POST", "/orders/row/delete/bulk/undo", json=row_ids)
        return resp.text

    def get_order_row_history(self, row_id: int) -> Any:
        """Retrieve history for an order row."""
        resp = self._request("GET", f"/orders/row/{row_id}/history")
        try:
            return resp.json()
        except Exception:
            return resp.text

    def export_orders(self, row_ids: list[int]) -> str:
        """Export order rows by IDs."""
        resp = self._request("POST", "/orders/export", json=row_ids)
        return resp.text

    # ── Product lists ────────────────────────────────────────────────

    def list_product_lists(self) -> list[ProductList]:
        """Retrieve index of all product lists."""
        resp = self._request("GET", "/productlist")
        data = resp.json()
        if isinstance(data, list):
            return [ProductList.from_dict(r) for r in data]
        return [ProductList.from_dict(r) for r in data.get("rows", data.get("results", []))]

    def create_product_list(self, name: str) -> ProductList:
        """Create a new empty product list."""
        resp = self._request("POST", "/productlist", json={"name": name})
        return ProductList.from_dict(resp.json())

    def delete_product_list(self, list_id: str) -> str:
        """Delete a product list."""
        resp = self._request("DELETE", f"/productlist/{list_id}")
        return resp.text

    def get_product_list_items(self, list_id: str) -> list[ProductListItem]:
        """Retrieve all items in a product list."""
        resp = self._request("GET", f"/productlist/{list_id}/items")
        data = resp.json()
        return [ProductListItem.from_dict(r) for r in data.get("rows", [])]

    def add_product_list_items(
        self, list_id: str, items: list[dict]
    ) -> list[dict]:
        """Add items to a product list (max 1000 per request).

        Each item dict must contain at least 'code' and 'brand'.
        Optional: supplier, category, description, price, listprice,
        purchaseprice, qta, warehouseposition, crosscodes, brandtocross.
        """
        if len(items) > 1000:
            raise BadRequestError("Maximum 1000 items per request", status_code=400)
        resp = self._request(
            "POST", f"/productlist/{list_id}/items", json={"rows": items}
        )
        return resp.json()

    def delete_product_list_items(
        self, list_id: str, items: list[dict[str, str]]
    ) -> str:
        """Remove items from a product list (max 1000 per request).

        Each item dict must contain 'code' and 'brand'.
        """
        if len(items) > 1000:
            raise BadRequestError("Maximum 1000 items per request", status_code=400)
        resp = self._request(
            "DELETE", f"/productlist/{list_id}/items", json={"rows": items}
        )
        return resp.text

    def update_product_list_items(
        self, list_id: str, items: list[dict]
    ) -> str:
        """Update items in a product list (max 1000 per request).

        Each item dict must contain 'code' and 'brand'.
        Optional: category, price, listprice, purchaseprice, qta, warehouseposition.
        """
        if len(items) > 1000:
            raise BadRequestError("Maximum 1000 items per request", status_code=400)
        resp = self._request(
            "PATCH", f"/productlist/{list_id}/items", json={"rows": items}
        )
        return resp.text

    # ── Search ───────────────────────────────────────────────────────

    def search_price_availability(
        self,
        supplier: str,
        skus: list[str],
        brand_input: str = "",
        qty: int = 1,
        user: str = "",
        password: str = "",
        respect_rate_limit: bool = True,
    ) -> list[SearchResult]:
        """Search price and availability from a supplier.

        Args:
            supplier: QRicambi supplier name.
            skus: Product codes to search (max 3).
            brand_input: Manufacturer filter.
            qty: Quantity for availability check.
            user: Supplier credentials (optional, uses keychain if omitted).
            password: Supplier credentials (optional, uses keychain if omitted).
            respect_rate_limit: If True, waits 30s between calls automatically.
        """
        if len(skus) > 3:
            raise BadRequestError("Maximum 3 SKUs per search request", status_code=400)

        if respect_rate_limit:
            elapsed = time.time() - self._last_search_time
            if elapsed < SEARCH_MIN_INTERVAL and self._last_search_time > 0:
                time.sleep(SEARCH_MIN_INTERVAL - elapsed)

        body: dict[str, Any] = {"supplier": supplier, "skus": skus, "qty": qty}
        if brand_input:
            body["brand_input"] = brand_input
        if user:
            body["user"] = user
        if password:
            body["password"] = password

        try:
            resp = self._request("POST", "/searchpriceandavailability", json=body)
        except BadRequestError as e:
            # Supplier login errors return 400 with "Incorrect login on ..."
            if "incorrect login" in str(e).lower():
                raise AuthenticationError(
                    f"Supplier credentials invalid: {e}", status_code=400
                ) from e
            raise
        self._last_search_time = time.time()
        try:
            data = resp.json()
        except Exception:
            return []
        if not data:
            return []
        if isinstance(data, dict):
            return [SearchResult.from_dict(data)]
        return [SearchResult.from_dict(r) for r in data]

    # ── Vehicle ──────────────────────────────────────────────────────

    def vehicle_by_plate(self, plate: str) -> VehicleInfo:
        """Look up vehicle information by Italian plate number."""
        plate = plate.upper().replace(" ", "")
        resp = self._request("GET", "/vehiclebyplate", params={"plate": plate})
        return VehicleInfo.from_dict(resp.json())
