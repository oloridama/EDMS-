from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from catalog.models.product_configuration import ProductConfiguration


@dataclass(frozen=True)
class Customer:
    customer_id: str
    name: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class SalesOrderStatus(Enum):
    CREATED = "created"
    PAID = "paid"
    PICKING = "picking"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    PACKED = "packed"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class SalesOrderLine:
    product_configuration: ProductConfiguration
    configuration_id: int
    quantity: int
    unit_price: Decimal
    fulfilled_quantity: int = 0
    dispatched_quantity: int = 0

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Sales-order quantity must be greater than zero.")
        if self.unit_price < 0:
            raise ValueError("Sales-order unit price cannot be negative.")
        if not 0 <= self.fulfilled_quantity <= self.quantity:
            raise ValueError("Fulfilled quantity must be between zero and ordered quantity.")
        if not 0 <= self.dispatched_quantity <= self.fulfilled_quantity:
            raise ValueError("Dispatched quantity must be between zero and fulfilled quantity.")

    @property
    def outstanding_quantity(self) -> int:
        return self.quantity - self.fulfilled_quantity

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity

    def fulfill(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Fulfilled quantity must be greater than zero.")
        if quantity > self.outstanding_quantity:
            raise ValueError("Fulfilled quantity exceeds the outstanding quantity.")
        self.fulfilled_quantity += quantity


@dataclass
class SalesOrder:
    customer: Customer
    warehouse_id: str
    lines: list[SalesOrderLine]
    status: SalesOrderStatus = field(default=SalesOrderStatus.CREATED, init=False)
    order_id: int | None = field(default=None, init=False)

    @property
    def total(self) -> Decimal:
        return sum((line.line_total for line in self.lines), start=Decimal("0.00"))

    def mark_paid(self) -> None:
        self._transition(SalesOrderStatus.CREATED, SalesOrderStatus.PAID)

    def start_picking(self) -> None:
        if self.status is SalesOrderStatus.PAID or (
            self.status is SalesOrderStatus.DELIVERED
            and any(line.outstanding_quantity for line in self.lines)
        ):
            self.status = SalesOrderStatus.PICKING
            return
        raise ValueError(
            f"Cannot move sales order from '{self.status.value}' "
            f"to '{SalesOrderStatus.PICKING.value}'."
        )

    def mark_packed(self) -> None:
        if self.status not in {
            SalesOrderStatus.PICKING,
            SalesOrderStatus.PARTIALLY_FULFILLED,
        }:
            raise ValueError("Only picking or partially fulfilled orders can be packed.")
        self.status = SalesOrderStatus.PACKED

    def dispatch(self) -> None:
        self._transition(SalesOrderStatus.PACKED, SalesOrderStatus.DISPATCHED)

    def deliver(self) -> None:
        self._transition(SalesOrderStatus.DISPATCHED, SalesOrderStatus.DELIVERED)

    def complete(self) -> None:
        if any(line.dispatched_quantity < line.quantity for line in self.lines):
            raise ValueError("An order cannot be completed before all quantities are dispatched.")
        self._transition(SalesOrderStatus.DELIVERED, SalesOrderStatus.COMPLETED)

    def record_fulfillment(self, line: SalesOrderLine, quantity: int) -> None:
        if self.status not in {
            SalesOrderStatus.PICKING,
            SalesOrderStatus.PARTIALLY_FULFILLED,
        }:
            raise ValueError("Fulfillment can only be recorded while picking an order.")
        if not any(existing is line for existing in self.lines):
            raise ValueError("The sales-order line does not belong to this order.")
        line.fulfill(quantity)
        self.status = (
            SalesOrderStatus.PARTIALLY_FULFILLED
            if any(item.outstanding_quantity for item in self.lines)
            else SalesOrderStatus.PICKING
        )

    def record_dispatch(self) -> dict[int, int]:
        if self.status is not SalesOrderStatus.PACKED:
            raise ValueError("Only packed orders can be dispatched.")
        dispatched = {}
        for line in self.lines:
            quantity = line.fulfilled_quantity - line.dispatched_quantity
            if quantity:
                line.dispatched_quantity += quantity
                dispatched[line.configuration_id] = (
                    dispatched.get(line.configuration_id, 0) + quantity
                )
        if not dispatched:
            raise ValueError("There are no fulfilled quantities ready for dispatch.")
        self.status = SalesOrderStatus.DISPATCHED
        return dispatched

    def _transition(self, expected: SalesOrderStatus, target: SalesOrderStatus) -> None:
        if self.status is not expected:
            raise ValueError(
                f"Cannot move sales order from '{self.status.value}' to '{target.value}'."
            )
        self.status = target
