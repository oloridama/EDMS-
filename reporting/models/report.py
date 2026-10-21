from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class InventoryLevelReport:
    product_configuration_id: str
    warehouse_id: str
    available_quantity: int
    reserved_quantity: int
    damaged_quantity: int
    expired_quantity: int


@dataclass(frozen=True)
class SalesSummaryReport:
    status: str
    order_count: int
    total_value: Decimal


@dataclass(frozen=True)
class ProcurementSummaryReport:
    status: str
    order_count: int
    total_value: Decimal
    ordered_quantity: int
    received_quantity: int


@dataclass(frozen=True)
class StockMovementSummaryReport:
    movement_type: str
    movement_count: int
    total_quantity: int
