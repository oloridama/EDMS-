from dataclasses import dataclass, field
from decimal import Decimal

from catalog.models.product_configuration import ProductConfiguration
from procurement.models.manufacturer import Manufacturer
@dataclass
class PurchaseLine:
    """
    A model of the purchase line; just name for now
    """
    product: ProductConfiguration
    quantity: int
    manufacturer: Manufacturer
    unit_price: Decimal
    _received_quantity: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Purchase-line quantity must be greater than zero.")
        if self.unit_price < 0:
            raise ValueError("Purchase-line unit price cannot be negative.")

    @property
    def received_quantity(self) -> int:
        return self._received_quantity

    @property
    def outstanding_quantity(self) -> int:
        return self.quantity - self.received_quantity

    @property
    def is_fully_received(self) -> bool:
        return self.received_quantity == self.quantity

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity

    def receive(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Received quantity must be greater than zero.")
        if quantity > self.outstanding_quantity:
            raise ValueError("Received quantity exceeds the outstanding quantity.")
        self._received_quantity += quantity