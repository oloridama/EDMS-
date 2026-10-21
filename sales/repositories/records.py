from __future__ import annotations

from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from catalog.repositories.records import ProductConfigurationRecord
from shared.database import Base


class CustomerRecord(Base):
    __tablename__ = "sales_customers"

    customer_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)


class SalesOrderRecord(Base):
    __tablename__ = "sales_orders"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_sales_orders_total_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("sales_customers.customer_id"))
    warehouse_id: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(40))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    customer: Mapped[CustomerRecord] = relationship()
    lines: Mapped[list[SalesOrderLineRecord]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class SalesOrderLineRecord(Base):
    __tablename__ = "sales_order_lines"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sales_order_lines_quantity_positive"),
        CheckConstraint(
            "fulfilled_quantity >= 0 AND fulfilled_quantity <= quantity",
            name="ck_sales_order_lines_fulfilled_quantity_valid",
        ),
        CheckConstraint(
            "dispatched_quantity >= 0 AND dispatched_quantity <= fulfilled_quantity",
            name="ck_sales_order_lines_dispatched_quantity_valid",
        ),
        CheckConstraint("unit_price >= 0", name="ck_sales_order_lines_price_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"), index=True)
    configuration_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_product_configurations.id")
    )
    quantity: Mapped[int] = mapped_column(Integer)
    fulfilled_quantity: Mapped[int] = mapped_column(Integer, default=0)
    dispatched_quantity: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    order: Mapped[SalesOrderRecord] = relationship(back_populates="lines")
    configuration: Mapped[ProductConfigurationRecord] = relationship(lazy="joined")
