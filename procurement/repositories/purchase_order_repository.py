from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from procurement.models.purchase_order import PurchaseOrder
from shared.database import Base


class PurchaseOrderRecord(Base):
    """SQLAlchemy persistence representation of a purchase order."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_purchase_orders_total_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(40))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    lines: Mapped[list["PurchaseOrderLineRecord"]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PurchaseOrderLineRecord(Base):
    """Persisted line details and the quantities actually received."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        UniqueConstraint(
            "purchase_order_id",
            "product_id",
            name="uq_purchase_order_lines_order_product",
        ),
        CheckConstraint("quantity > 0", name="ck_purchase_order_lines_quantity_positive"),
        CheckConstraint(
            "received_quantity >= 0 AND received_quantity <= quantity",
            name="ck_purchase_order_lines_received_quantity_valid",
        ),
        CheckConstraint("unit_price >= 0", name="ck_purchase_order_lines_price_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id"),
    )
    product_id: Mapped[str] = mapped_column(String(100))
    product_name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int] = mapped_column(Integer)
    received_quantity: Mapped[int] = mapped_column(Integer)
    manufacturer_name: Mapped[str] = mapped_column(String(200))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    purchase_order: Mapped[PurchaseOrderRecord] = relationship(back_populates="lines")


class PurchaseOrderRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_purchase_line(self, purchase_order_id: int, product_id: str):
        """Fetch a persisted purchase line by its product identity within an order."""
        statement = select(PurchaseOrderLineRecord).where(
            PurchaseOrderLineRecord.purchase_order_id == purchase_order_id,
            PurchaseOrderLineRecord.product_id == product_id,
        )
        line = self.db_session.scalar(statement)
        if line is not None:
            return line

        order_exists = self.db_session.scalar(
            select(PurchaseOrderRecord.id).where(
                PurchaseOrderRecord.id == purchase_order_id
            )
        )
        if order_exists is None:
            raise ValueError(f"Purchase order {purchase_order_id} was not found.")

        raise ValueError(
            f"Purchase line for product '{product_id}' was not found in order {purchase_order_id}."
        )

    def save_purchase_order(self, purchase_order: PurchaseOrder) -> int:
        """Stage an order and its lines in the current transaction."""
        record = PurchaseOrderRecord(
            supplier_name=purchase_order.supplier.name,
            status=purchase_order.status.value,
            total=purchase_order.total,
            lines=[
                self._to_line_record(line)
                for line in purchase_order.purchase_lines
            ],
        )
        self.db_session.add(record)

        # flush sends INSERT statements and obtains the generated ID, but does not commit.
        self.db_session.flush()
        purchase_order.id = record.id
        return record.id

    def get_purchase_order(self, purchase_order_id: int) -> PurchaseOrderRecord | None:
        statement = select(PurchaseOrderRecord).where(
            PurchaseOrderRecord.id == purchase_order_id
        )
        return self.db_session.scalar(statement)

    def delete_purchase_order(self, purchase_order_id: int):
        """Delete a purchase order and its lines from the database."""
        order = self.get_purchase_order(purchase_order_id)
        if order is None:
            raise ValueError(f"Purchase order {purchase_order_id} was not found.")
        self.db_session.delete(order)

    @staticmethod
    def _to_line_record(line) -> PurchaseOrderLineRecord:
        configuration = line.product
        product = getattr(configuration, "product", None)
        return PurchaseOrderLineRecord(
            product_id=getattr(product, "product_id", None),
            product_name=getattr(product, "name", None),
            quantity=line.quantity,
            received_quantity=line.received_quantity,
            manufacturer_name=line.manufacturer.name,
            unit_price=line.unit_price,
        )