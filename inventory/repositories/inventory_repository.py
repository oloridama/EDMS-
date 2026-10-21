from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship, selectinload

from inventory.models.inventory import InventoryLot, StockMovement, StockMovementType
from shared.database import Base


class InventoryLotRecord(Base):
    """SQLAlchemy record representing a stock lot stored in the database."""

    __tablename__ = "inventory_lots"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_inventory_lots_quantity_nonnegative"),
        CheckConstraint(
            "available_quantity >= 0",
            name="ck_inventory_lots_available_quantity_nonnegative",
        ),
        CheckConstraint(
            "reserved_quantity >= 0",
            name="ck_inventory_lots_reserved_quantity_nonnegative",
        ),
        CheckConstraint(
            "damaged_quantity >= 0",
            name="ck_inventory_lots_damaged_quantity_nonnegative",
        ),
        CheckConstraint(
            "expired_quantity >= 0",
            name="ck_inventory_lots_expired_quantity_nonnegative",
        ),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    product_configuration_id: Mapped[str] = mapped_column(String(100), index=True)
    warehouse_id: Mapped[str] = mapped_column(String(100), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer)
    available_quantity: Mapped[int] = mapped_column(Integer)
    reserved_quantity: Mapped[int] = mapped_column(Integer)
    damaged_quantity: Mapped[int] = mapped_column(Integer)
    expired_quantity: Mapped[int] = mapped_column(Integer)
    movements: Mapped[list["InventoryMovementRecord"]] = relationship(
        back_populates="lot",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class InventoryMovementRecord(Base):
    """Persistence record for a stock movement event."""

    __tablename__ = "inventory_movements"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_movements_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lot_id: Mapped[str] = mapped_column(ForeignKey("inventory_lots.id"), index=True)
    movement_type: Mapped[str] = mapped_column(String(40))
    quantity: Mapped[int] = mapped_column(Integer)
    reference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
    lot: Mapped[InventoryLotRecord] = relationship(back_populates="movements")


class InventoryLotRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def save_inventory_lot(self, lot: InventoryLot) -> str:
        """Persist a domain lot and its movement timeline to the current session."""
        record = self.get_inventory_lot(lot.id)
        if record is None:
            record = InventoryLotRecord(
                id=lot.id,
                product_configuration_id=lot.product_configuration_id,
                warehouse_id=lot.warehouse_id,
                received_at=lot.received_at,
                expiry_date=lot.expiry_date,
                quantity=lot.quantity,
                available_quantity=lot.available_quantity,
                reserved_quantity=lot.reserved_quantity,
                damaged_quantity=lot.damaged_quantity,
                expired_quantity=lot.expired_quantity,
            )
            self.db_session.add(record)
        else:
            record.product_configuration_id = lot.product_configuration_id
            record.warehouse_id = lot.warehouse_id
            record.received_at = lot.received_at
            record.expiry_date = lot.expiry_date
            record.quantity = lot.quantity
            record.available_quantity = lot.available_quantity
            record.reserved_quantity = lot.reserved_quantity
            record.damaged_quantity = lot.damaged_quantity
            record.expired_quantity = lot.expired_quantity

        record.movements = [
            self._to_movement_record(movement, lot_id=record.id)
            for movement in lot.movements
        ]

        self.db_session.flush()
        return record.id

    def get_inventory_lot(self, lot_id: str) -> InventoryLotRecord | None:
        statement = (
            select(InventoryLotRecord)
            .options(selectinload(InventoryLotRecord.movements))
            .where(InventoryLotRecord.id == lot_id)
        )
        return self.db_session.scalar(statement)

    def get_lots_for_product(
        self,
        product_configuration_id: str,
        warehouse_id: str | None = None,
    ) -> list[InventoryLotRecord]:
        statement = (
            select(InventoryLotRecord)
            .options(selectinload(InventoryLotRecord.movements))
            .where(InventoryLotRecord.product_configuration_id == product_configuration_id)
        )
        if warehouse_id is not None:
            statement = statement.where(InventoryLotRecord.warehouse_id == warehouse_id)
        return list(self.db_session.scalars(statement))

    def get_available_stock(self, product_configuration_id: str, warehouse_id: str) -> int:
        statement = select(InventoryLotRecord).where(
            InventoryLotRecord.product_configuration_id == product_configuration_id,
            InventoryLotRecord.warehouse_id == warehouse_id,
        )
        records = self.db_session.scalars(statement).all()
        return sum(record.available_quantity for record in records)

    def reserve_stock(
        self,
        product_configuration_id: str,
        warehouse_id: str,
        quantity: int,
        reference_id: str,
    ) -> None:
        lots = self._get_stock_lots(product_configuration_id, warehouse_id)
        if sum(lot.available_quantity for lot in lots) < quantity:
            raise ValueError(
                f"Insufficient available stock for configuration '{product_configuration_id}'."
            )
        remaining = quantity
        for lot in lots:
            reserved = min(lot.available_quantity, remaining)
            if not reserved:
                continue
            lot.available_quantity -= reserved
            lot.reserved_quantity += reserved
            lot.movements.append(
                InventoryMovementRecord(
                    movement_type=StockMovementType.RESERVATION.value,
                    quantity=reserved,
                    reference_id=reference_id,
                    note="Sales order paid; stock reserved",
                    occurred_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
            )
            remaining -= reserved
            if not remaining:
                break
        self.db_session.flush()

    def release_reserved_stock(
        self,
        product_configuration_id: str,
        warehouse_id: str,
        quantity: int,
        reference_id: str,
    ) -> None:
        lots = self._get_stock_lots(product_configuration_id, warehouse_id)
        if sum(lot.reserved_quantity for lot in lots) < quantity:
            raise ValueError(
                f"Insufficient reserved stock for configuration '{product_configuration_id}'."
            )
        remaining = quantity
        for lot in lots:
            released = min(lot.reserved_quantity, remaining)
            if not released:
                continue
            lot.reserved_quantity -= released
            lot.available_quantity += released
            lot.movements.append(
                InventoryMovementRecord(
                    movement_type=StockMovementType.RELEASE.value,
                    quantity=released,
                    reference_id=reference_id,
                    note="Sales order cancelled; reservation released",
                    occurred_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
            )
            remaining -= released
            if not remaining:
                break
        self.db_session.flush()

    def dispatch_reserved_stock(
        self,
        product_configuration_id: str,
        warehouse_id: str,
        quantity: int,
        reference_id: str,
    ) -> None:
        lots = self._get_stock_lots(product_configuration_id, warehouse_id)
        if sum(lot.reserved_quantity for lot in lots) < quantity:
            raise ValueError(
                f"Insufficient reserved stock for configuration '{product_configuration_id}'."
            )
        remaining = quantity
        for lot in lots:
            dispatched = min(lot.reserved_quantity, remaining)
            if not dispatched:
                continue
            lot.reserved_quantity -= dispatched
            lot.quantity -= dispatched
            lot.movements.append(
                InventoryMovementRecord(
                    movement_type=StockMovementType.DISPATCH.value,
                    quantity=dispatched,
                    reference_id=reference_id,
                    note="Sales order dispatched",
                    occurred_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
            )
            remaining -= dispatched
            if not remaining:
                break
        self.db_session.flush()

    def _get_stock_lots(
        self,
        product_configuration_id: str,
        warehouse_id: str,
    ) -> list[InventoryLotRecord]:
        statement = (
            select(InventoryLotRecord)
            .options(selectinload(InventoryLotRecord.movements))
            .where(
                InventoryLotRecord.product_configuration_id == product_configuration_id,
                InventoryLotRecord.warehouse_id == warehouse_id,
            )
            .order_by(InventoryLotRecord.expiry_date, InventoryLotRecord.received_at)
            .with_for_update()
        )
        return list(self.db_session.scalars(statement))

    @staticmethod
    def _to_movement_record(
        movement: StockMovement,
        lot_id: str,
    ) -> InventoryMovementRecord:
        return InventoryMovementRecord(
            lot_id=lot_id,
            movement_type=movement.movement_type.value,
            quantity=movement.quantity,
            reference_id=movement.reference_id,
            note=movement.note,
            occurred_at=movement.occurred_at,
        )

    @staticmethod
    def from_record(record: InventoryLotRecord) -> InventoryLot:
        """Map a persisted lot back into its domain representation."""
        lot = InventoryLot(
            id=record.id,
            product_configuration_id=record.product_configuration_id,
            warehouse_id=record.warehouse_id,
            received_at=record.received_at,
            expiry_date=record.expiry_date,
            quantity=record.quantity,
            available_quantity=record.available_quantity,
            reserved_quantity=record.reserved_quantity,
            damaged_quantity=record.damaged_quantity,
            expired_quantity=record.expired_quantity,
        )
        for movement in record.movements:
            lot.movements.append(
                StockMovement(
                    movement_type=StockMovementType(movement.movement_type),
                    quantity=movement.quantity,
                    reference_id=movement.reference_id,
                    note=movement.note,
                    occurred_at=movement.occurred_at,
                )
            )
        return lot
