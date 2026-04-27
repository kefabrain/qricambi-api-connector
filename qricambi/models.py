"""Data models for QRicambi API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── Supplier ─────────────────────────────────────────────────────────

@dataclass
class Supplier:
    name: str
    login_url: str = ""
    is_enable: bool = False
    has_more_than_two_credentials: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> Supplier:
        return cls(
            name=d.get("name", ""),
            login_url=d.get("loginUrl", ""),
            is_enable=d.get("isEnable", False),
            has_more_than_two_credentials=d.get("hasMoreThanTwoCredentials", False),
        )


@dataclass
class CheckSupplierResult:
    authenticated: bool
    message: str = ""
    supplier: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> CheckSupplierResult:
        return cls(
            authenticated=d.get("authenticated", False),
            message=d.get("message", ""),
            supplier=d.get("supplier", ""),
        )


# ── Entity extraction ────────────────────────────────────────────────

@dataclass
class EntityResult:
    entity_type: str
    text: str

    @classmethod
    def from_dict(cls, d: dict) -> EntityResult:
        return cls(
            entity_type=d.get("entity_type", ""),
            text=d.get("text", ""),
        )


# ── Orders ───────────────────────────────────────────────────────────

@dataclass
class OrderStatus:
    id: int = 0
    name: str = ""

    @classmethod
    def from_dict(cls, d: dict | None) -> OrderStatus:
        if not d:
            return cls()
        return cls(id=d.get("id", 0), name=d.get("name", ""))


@dataclass
class OrderCustomer:
    id: int = 0
    customer_code: str = ""
    customer_name: str = ""
    email: str = ""
    phone: str = ""
    vat: str = ""

    @classmethod
    def from_dict(cls, d: dict | None) -> OrderCustomer:
        if not d:
            return cls()
        return cls(
            id=d.get("id", 0),
            customer_code=d.get("customerCode", ""),
            customer_name=d.get("customerName", ""),
            email=d.get("email", ""),
            phone=d.get("phone", ""),
            vat=d.get("vat", ""),
        )


@dataclass
class OrderRow:
    id: int = 0
    account_id: int = 0
    q_order_number: str = ""
    supplier_order_number: str = ""
    qty: int = 0
    note: str = ""
    customer_id: int | None = None
    status_id: int = 0
    from_search_row: dict | None = None
    created_at: str = ""
    updated_at: str = ""
    confirmed_at: str = ""
    deleted_at: str = ""
    customer: OrderCustomer | None = None
    status: OrderStatus | None = None

    @classmethod
    def from_dict(cls, d: dict) -> OrderRow:
        cid = d.get("customerid")
        if isinstance(cid, dict):
            cid = cid.get("int64") if cid.get("valid") else None
        return cls(
            id=d.get("id", 0),
            account_id=d.get("accountID", 0),
            q_order_number=d.get("qordernumber", ""),
            supplier_order_number=d.get("supplierordernumber", ""),
            qty=d.get("qty", 0),
            note=d.get("note", ""),
            customer_id=cid,
            status_id=d.get("statusid", 0),
            from_search_row=d.get("fromsearchrow"),
            created_at=d.get("create_at", ""),
            updated_at=d.get("update_at", ""),
            confirmed_at=d.get("confirm_at", ""),
            deleted_at=d.get("delete_at", ""),
            customer=OrderCustomer.from_dict(d.get("customer")),
            status=OrderStatus.from_dict(d.get("status")),
        )


# ── Product lists ────────────────────────────────────────────────────

@dataclass
class ProductList:
    id: str = ""
    name: str = ""
    created_at: str = ""
    updated_at: str = ""
    active: bool = True
    filename: str = ""
    status_import: str = ""
    type_conf: str = ""
    expire_date: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> ProductList:
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            created_at=d.get("createdat", ""),
            updated_at=d.get("updatedat", ""),
            active=d.get("active", True),
            filename=d.get("filename", ""),
            status_import=d.get("statusimport", ""),
            type_conf=d.get("typeconf", ""),
            expire_date=d.get("expiredate", ""),
        )


@dataclass
class ProductListItem:
    code: str = ""
    brand: str = ""
    supplier: str = ""
    category: str = ""
    description: str = ""
    price: float = 0.0
    list_price: float = 0.0
    purchase_price: float = 0.0
    qty: int = 0
    warehouse_position: str = ""
    cross_codes: list[str] = field(default_factory=list)
    url: str = ""
    url_image: str = ""
    source_name: str = ""
    supplier_conf_id: int = 0
    only_append: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> ProductListItem:
        pp = d.get("purchaseprice", 0)
        if isinstance(pp, str):
            try:
                pp = float(pp)
            except ValueError:
                pp = 0.0
        return cls(
            code=d.get("code", ""),
            brand=d.get("brand", ""),
            supplier=d.get("supplier", ""),
            category=d.get("category", ""),
            description=d.get("description", ""),
            price=d.get("price", 0) or 0,
            list_price=d.get("listprice", 0) or 0,
            purchase_price=pp,
            qty=d.get("qta", 0) or 0,
            warehouse_position=d.get("warehouseposition", ""),
            cross_codes=d.get("crosscodes") or [],
            url=d.get("URL", ""),
            url_image=d.get("URLimage", ""),
            source_name=d.get("sourcename", ""),
            supplier_conf_id=d.get("supplierconfid", 0),
            only_append=d.get("onlyappend", False),
        )


# ── Search ───────────────────────────────────────────────────────────

@dataclass
class SupplierAvailability:
    code: int = 0
    description: str = ""

    @classmethod
    def from_dict(cls, d: dict | None) -> SupplierAvailability:
        if not d:
            return cls()
        return cls(
            code=d.get("Availability_code", 0),
            description=d.get("Availability_desc", ""),
        )

    @property
    def is_available(self) -> bool:
        return self.code == 99


@dataclass
class SearchResult:
    supplier: str = ""
    code: str = ""
    from_code: str = ""
    description: str = ""
    brand_input: str = ""
    manufacturer: str = ""
    manufacturer_tagged: str = ""
    price: float = 0.0
    web_price: float = 0.0
    retail_price: float = 0.0
    promo: bool = False
    promo_text: str = ""
    link: str = ""
    code_alternatives: str = ""
    category_tagged: str = ""
    matched: bool = False
    qty_input: int = 0
    availability: SupplierAvailability | None = None
    supplier_custom_name: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> SearchResult:
        return cls(
            supplier=d.get("Supplier", ""),
            code=d.get("Code", ""),
            from_code=d.get("From_code", ""),
            description=d.get("Description", ""),
            brand_input=d.get("Brand_input", ""),
            manufacturer=d.get("Manufacturer", ""),
            manufacturer_tagged=d.get("Manufacturer_tagged", ""),
            price=d.get("Price", 0) or 0,
            web_price=d.get("Web_price", 0) or 0,
            retail_price=d.get("Retail_price", 0) or 0,
            promo=d.get("Promo", False),
            promo_text=d.get("Promo_text", ""),
            link=d.get("Link", ""),
            code_alternatives=d.get("Code_alternatives", ""),
            category_tagged=d.get("Category_tagged", ""),
            matched=d.get("Matched", False),
            qty_input=d.get("Qty_input", 0),
            availability=SupplierAvailability.from_dict(d.get("Availability")),
            supplier_custom_name=d.get("Supplier_customname", ""),
        )


# ── Vehicle ──────────────────────────────────────────────────────────

@dataclass
class VehicleInfo:
    plate: str = ""
    vin: str = ""
    manufacturer: str = ""
    model: str = ""
    car_descr: str = ""
    car_type: str = ""
    body_type: str = ""
    doors: str = ""
    cc: str = ""
    cylinders: str = ""
    valves: str = ""
    hp: str = ""
    kw: str = ""
    engine_code: str = ""
    engine_type: str = ""
    engine_details: str = ""
    fuel_system: str = ""
    fuel_supply: str = ""
    wheel_drive: str = ""
    gearbox: str = ""
    registration_date: str = ""
    production_date_from: str = ""
    production_date_to: str = ""
    region: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> VehicleInfo:
        return cls(
            plate=d.get("plate", ""),
            vin=d.get("vin", ""),
            manufacturer=d.get("manufacturer", ""),
            model=d.get("model", ""),
            car_descr=d.get("cardescr", ""),
            car_type=d.get("cartype", ""),
            body_type=d.get("bodytype", ""),
            doors=d.get("doors", ""),
            cc=d.get("cc", ""),
            cylinders=d.get("cylinders", ""),
            valves=d.get("valves", ""),
            hp=d.get("hp", ""),
            kw=d.get("kw", ""),
            engine_code=d.get("enginecode", ""),
            engine_type=d.get("enginetype", ""),
            engine_details=d.get("enginedetails", ""),
            fuel_system=d.get("fuelsystem", ""),
            fuel_supply=d.get("fuelsupply", ""),
            wheel_drive=d.get("wheeldrive", ""),
            gearbox=d.get("gearbox", ""),
            registration_date=d.get("immatrdate", ""),
            production_date_from=d.get("productiondatefrom", ""),
            production_date_to=d.get("productiondateto", ""),
            region=d.get("region", ""),
        )
