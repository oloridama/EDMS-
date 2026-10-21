from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum


class StockMovementType(Enum):
    RECEIPT = "receipt"
    RESERVATION = "reservation"
    RELEASE = "release"
    DISPATCH = "dispatch"
    DAMAGE = "damage"
    EXPIRED = "expired"
    ADJUSTMENT = "adjustment"


@dataclass
class StockMovement:
    movement_type: StockMovementType
    quantity: int
    reference_id: str | None = None
    note: str | None = None
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Movement quantity must be greater than zero.")


@dataclass
class InventoryLot:
    """Inventory held for a specific product configuration at a warehouse."""

    id: str
    product_configuration_id: str
    warehouse_id: str
    received_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    expiry_date: date | None = None
    quantity: int = 0
    available_quantity: int = 0
    reserved_quantity: int = 0
    damaged_quantity: int = 0
    expired_quantity: int = 0
    movements: list[StockMovement] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError("Lot quantity cannot be negative.")
        if self.available_quantity < 0:
            raise ValueError("Available quantity cannot be negative.")
        if self.reserved_quantity < 0:
            raise ValueError("Reserved quantity cannot be negative.")
        if self.damaged_quantity < 0:
            raise ValueError("Damaged quantity cannot be negative.")
        if self.expired_quantity < 0:
            raise ValueError("Expired quantity cannot be negative.")

    @property
    def total_quantity(self) -> int:
        return (
            self.available_quantity
            + self.reserved_quantity
            + self.damaged_quantity
            + self.expired_quantity
        )

    def receive(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Received quantity must be greater than zero.")
        self.quantity += quantity
        self.available_quantity += quantity
        self.record_movement(
            movement_type=StockMovementType.RECEIPT,
            quantity=quantity,
            note="Inventory received",
        )

    def reserve(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Reserved quantity must be greater than zero.")
        if quantity > self.available_quantity:
            raise ValueError("Reservation exceeds available quantity.")
        self.available_quantity -= quantity
        self.reserved_quantity += quantity
        self.record_movement(
            movement_type=StockMovementType.RESERVATION,
            quantity=quantity,
            note="Inventory reserved",
        )

    def release_reservation(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Released quantity must be greater than zero.")
        if quantity > self.reserved_quantity:
            raise ValueError("Release exceeds reserved quantity.")
        self.reserved_quantity -= quantity
        self.available_quantity += quantity
        self.record_movement(
            movement_type=StockMovementType.RELEASE,
            quantity=quantity,
            note="Reservation released",
        )

    def dispatch(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Dispatch quantity must be greater than zero.")
        if quantity > self.reserved_quantity:
            raise ValueError("Dispatch exceeds reserved quantity.")
        self.reserved_quantity -= quantity
        self.quantity -= quantity
        self.record_movement(
            movement_type=StockMovementType.DISPATCH,
            quantity=quantity,
            note="Inventory dispatched",
        )

    def mark_damaged(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Damaged quantity must be greater than zero.")
        if quantity > self.available_quantity:
            raise ValueError("Damaged quantity exceeds available quantity.")
        self.available_quantity -= quantity
        self.damaged_quantity += quantity
        self.record_movement(
            movement_type=StockMovementType.DAMAGE,
            quantity=quantity,
            note="Inventory marked damaged",
        )

    def mark_expired(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Expired quantity must be greater than zero.")
        if quantity > self.available_quantity:
            raise ValueError("Expired quantity exceeds available quantity.")
        self.available_quantity -= quantity
        self.expired_quantity += quantity
        self.record_movement(
            movement_type=StockMovementType.EXPIRED,
            quantity=quantity,
            note="Inventory expired",
        )

    def record_movement(
        self,
        movement_type: StockMovementType,
        quantity: int,
        reference_id: str | None = None,
        note: str | None = None,
    ) -> StockMovement:
        movement = StockMovement(
            movement_type=movement_type,
            quantity=quantity,
            reference_id=reference_id,
            note=note,
        )
        self.movements.append(movement)
        return movement
