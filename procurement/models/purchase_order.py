from dataclasses import dataclass, field
from enum import Enum

from procurement.models.purchase_line import PurchaseLine
from procurement.models.supplier import Supplier


class PurchaseOrderStatus(Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"
    PARTIALLY_RECEIVED = "partially_received"
    COMPLETED = "completed"


@dataclass
class PurchaseOrder:
    supplier: Supplier
    purchase_lines: list[PurchaseLine]
    _status: PurchaseOrderStatus = field(default=PurchaseOrderStatus.DRAFT, init=False, repr=False)
    id: int | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        product_ids = [
            line.product.product.product_id
            for line in self.purchase_lines
        ]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("A purchase order cannot contain duplicate products.")

    @property
    def status(self) -> PurchaseOrderStatus:
        return self._status

    @property
    def total(self):
        """Calculate the order total from its lines to avoid duplicated state."""
        return sum((line.line_total for line in self.purchase_lines), start=0)

    @property
    def total_quantity_ordered(self) -> int:
        return sum(line.quantity for line in self.purchase_lines)

    @property
    def total_quantity_received(self) -> int:
        return sum(line.received_quantity for line in self.purchase_lines)

    @property
    def is_fully_fulfilled(self) -> bool:
        return all(line.is_fully_received for line in self.purchase_lines)

    def approve(self) -> None:
        if self.status is not PurchaseOrderStatus.DRAFT:
            raise ValueError("Only draft purchase orders can be approved.")
        if not self.purchase_lines:
            raise ValueError("A purchase order must contain at least one line.")
        self._status = PurchaseOrderStatus.APPROVED

    def send(self) -> None:
        if self.status is not PurchaseOrderStatus.APPROVED:
            raise ValueError("Only approved purchase orders can be sent.")
        self._status = PurchaseOrderStatus.SENT

    def receive(self, line: PurchaseLine, quantity: int) -> None:
        if self.status not in {
            PurchaseOrderStatus.SENT,
            PurchaseOrderStatus.PARTIALLY_RECEIVED,
        }:
            raise ValueError("Only sent purchase orders can receive goods.")
        if not any(existing_line is line for existing_line in self.purchase_lines):
            raise ValueError("The purchase line does not belong to this order.")

        line.receive(quantity)
        if self.is_fully_fulfilled:
            self._status = PurchaseOrderStatus.COMPLETED
        else:
            self._status = PurchaseOrderStatus.PARTIALLY_RECEIVED

    def complete(self) -> None:
        """Close a partially received order without erasing its quantity shortfall."""
        if self.status is not PurchaseOrderStatus.PARTIALLY_RECEIVED:
            raise ValueError("Only partially received purchase orders can be closed this way.")
        if self.total_quantity_received == 0:
            raise ValueError("A partially completed order must have received some goods.")

        # Completion closes the procurement cycle; line quantities retain the actual fulfillment.
        self._status = PurchaseOrderStatus.COMPLETED