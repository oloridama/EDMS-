from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class SpecificationTypeIn(BaseModel):
    name: str
    value_type: str
    allowed_values: list[Any] = Field(default_factory=list)


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None
    specification_types: list[SpecificationTypeIn] = Field(default_factory=list)


class ProductCreate(BaseModel):
    product_id: str
    name: str
    description: str
    brand_name: str
    category_name: str


class PricingRuleIn(BaseModel):
    min_quantity: int | None = None
    max_quantity: int | None = None
    unit_price: Decimal


class ConfigurationCreate(BaseModel):
    product_id: str
    specifications: dict[str, Any] = Field(default_factory=dict)
    pricing_rules: list[PricingRuleIn] = Field(default_factory=list)
    material: str | None = None
    weight: float | None = None
    color: str | None = None
    size: str | None = None
    volume: float | None = None
    length: float | None = None
    width: float | None = None
    unit: str | None = None
    additional_features: str | None = None


class PriceUpdate(BaseModel):
    unit_price: Decimal


class LotCreate(BaseModel):
    lot_id: str
    configuration_id: int
    warehouse_id: str
    quantity: int
    expiry_date: date | None = None


class LotResponse(BaseModel):
    id: str
    configuration_id: str
    warehouse_id: str
    quantity: int
    available_quantity: int
    reserved_quantity: int
    damaged_quantity: int
    expired_quantity: int


class CustomerIn(BaseModel):
    customer_id: str
    name: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class SalesLineIn(BaseModel):
    configuration_id: int
    quantity: int
    unit_price: Decimal | None = None


class SalesOrderCreate(BaseModel):
    customer: CustomerIn
    warehouse_id: str
    lines: list[SalesLineIn]


class FulfillRequest(BaseModel):
    configuration_id: int
    quantity: int


class SalesLineResponse(BaseModel):
    configuration_id: int
    quantity: int
    unit_price: Decimal
    fulfilled_quantity: int
    dispatched_quantity: int


class SalesOrderResponse(BaseModel):
    order_id: int
    customer_id: str
    warehouse_id: str
    status: str
    total: Decimal
    lines: list[SalesLineResponse]


class SupplierIn(BaseModel):
    name: str
    address: str
    email: str
    phone: str


class PurchaseLineIn(BaseModel):
    configuration_id: int
    quantity: int
    manufacturer_name: str
    unit_price: Decimal


class PurchaseOrderCreate(BaseModel):
    supplier: SupplierIn
    lines: list[PurchaseLineIn]


class StatusUpdate(BaseModel):
    status: str


class PurchaseLineResponse(BaseModel):
    product_id: str | None
    product_name: str | None
    quantity: int
    received_quantity: int
    manufacturer_name: str
    unit_price: Decimal


class PurchaseOrderResponse(BaseModel):
    order_id: int
    supplier_name: str
    status: str
    total: Decimal
    lines: list[PurchaseLineResponse]


class TransporterCreate(BaseModel):
    name: str
    contact_number: str
    email: str
    address: str
    transportation_type: str
    marital_status: str | None = None
    dob: str | None = None
    citizenship: str | None = None


class ModeOfTransportIn(BaseModel):
    name: str
    reg_no: str
    length: float
    width: float
    height: float


class ShipmentCreate(BaseModel):
    tracking_id: str
    eta: datetime | None = None
    configuration_ids: list[int]
    transporter_id: str
    transporter_name: str
    mode_of_transport: ModeOfTransportIn


class ShipmentResponse(BaseModel):
    tracking_id: str
    eta: datetime | None
    status: str
    transporter_id: str
    transporter_name: str
    mode: str
    configuration_ids: list[int]


class ShipmentStatusUpdate(BaseModel):
    status: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "sales_officer"


class BootstrapRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: str
    is_active: bool
    permissions: list[str]


class BootstrapRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: str
    is_active: bool
    permissions: list[str]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
