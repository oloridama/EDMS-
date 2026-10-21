from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from catalog.repositories.records import ProductConfigurationRecord
from shared.database import Base


class TransporterRecord(Base):
    __tablename__ = "logistics_transporters"

    transporter_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    contact_number: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    address: Mapped[str] = mapped_column(String(500))
    transportation_type: Mapped[str] = mapped_column(String(100))
    marital_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dob: Mapped[str | None] = mapped_column(String(30), nullable=True)
    citizenship: Mapped[str | None] = mapped_column(String(100), nullable=True)


class LogisticRecord(Base):
    __tablename__ = "logistics_shipments"

    tracking_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    eta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(40))
    transporter_id: Mapped[str] = mapped_column(String(100))
    transporter_name_at_dispatch: Mapped[str] = mapped_column(String(200))
    mode_name_at_dispatch: Mapped[str] = mapped_column(String(100))
    mode_reg_no_at_dispatch: Mapped[str] = mapped_column(String(100))
    mode_length_at_dispatch: Mapped[float]
    mode_width_at_dispatch: Mapped[float]
    mode_height_at_dispatch: Mapped[float]
    package: Mapped[list[LogisticPackageRecord]] = relationship(
        back_populates="shipment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class LogisticPackageRecord(Base):
    __tablename__ = "logistics_shipment_configurations"
    __table_args__ = (
        CheckConstraint("shipment_id != ''", name="ck_logistics_package_shipment_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("logistics_shipments.tracking_id"))
    configuration_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_product_configurations.id")
    )
    shipment: Mapped[LogisticRecord] = relationship(back_populates="package")
    configuration: Mapped[ProductConfigurationRecord] = relationship(lazy="joined")
