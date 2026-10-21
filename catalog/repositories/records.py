from __future__ import annotations

from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class CategoryRecord(Base):
    __tablename__ = "catalog_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    specification_types: Mapped[list[SpecificationTypeRecord]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    products: Mapped[list[ProductRecord]] = relationship(back_populates="category")


class SpecificationTypeRecord(Base):
    __tablename__ = "catalog_specification_types"
    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_catalog_spec_type_category_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("catalog_categories.id"))
    name: Mapped[str] = mapped_column(String(200))
    value_type: Mapped[str] = mapped_column(String(30))
    allowed_values: Mapped[list[str | int | float | bool]] = mapped_column(JSON, default=list)
    category: Mapped[CategoryRecord] = relationship(back_populates="specification_types")
    configurations: Mapped[list[ConfigurationSpecificationRecord]] = relationship(
        back_populates="specification_type"
    )
    specifications: Mapped[list[SpecificationValueRecord]] = relationship(
        back_populates="specification_type"
    )


class SpecificationValueRecord(Base):
    __tablename__ = "catalog_specifications"
    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "specification_type_id",
            "value",
            name="uq_catalog_specification_category_type_value",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("catalog_categories.id"))
    specification_type_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_specification_types.id")
    )
    value: Mapped[str | int | float | bool] = mapped_column(JSON)
    specification_type: Mapped[SpecificationTypeRecord] = relationship(
        back_populates="specifications",
        lazy="joined",
    )


class ProductRecord(Base):
    __tablename__ = "catalog_products"

    product_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(String(1000))
    brand_name: Mapped[str] = mapped_column(String(200), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("catalog_categories.id"))
    category: Mapped[CategoryRecord] = relationship(back_populates="products", lazy="selectin")
    configurations: Mapped[list[ProductConfigurationRecord]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ProductConfigurationRecord(Base):
    __tablename__ = "catalog_product_configurations"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("catalog_products.product_id"), index=True)
    material: Mapped[str | None] = mapped_column(String(200), nullable=True)
    weight: Mapped[float | None]
    color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    volume: Mapped[float | None]
    length: Mapped[float | None]
    width: Mapped[float | None]
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    additional_features: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    product: Mapped[ProductRecord] = relationship(back_populates="configurations")
    specifications: Mapped[list[ConfigurationSpecificationRecord]] = relationship(
        back_populates="configuration",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    pricing_rules: Mapped[list[PricingRuleRecord]] = relationship(
        back_populates="configuration",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ConfigurationSpecificationRecord(Base):
    __tablename__ = "catalog_configuration_specifications"
    __table_args__ = (
        UniqueConstraint(
            "configuration_id",
            "specification_type_id",
            name="uq_catalog_config_spec_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    configuration_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_product_configurations.id")
    )
    specification_type_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_specification_types.id")
    )
    value: Mapped[str | int | float | bool] = mapped_column(JSON)
    configuration: Mapped[ProductConfigurationRecord] = relationship(
        back_populates="specifications"
    )
    specification_type: Mapped[SpecificationTypeRecord] = relationship(
        back_populates="configurations",
        lazy="joined",
    )


class PricingRuleRecord(Base):
    __tablename__ = "catalog_pricing_rules"
    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="ck_catalog_pricing_nonnegative"),
        CheckConstraint(
            "min_quantity IS NULL OR min_quantity > 0",
            name="ck_catalog_pricing_min_quantity_positive",
        ),
        CheckConstraint(
            "max_quantity IS NULL OR max_quantity >= min_quantity",
            name="ck_catalog_pricing_quantity_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    configuration_id: Mapped[int] = mapped_column(
        ForeignKey("catalog_product_configurations.id")
    )
    min_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    configuration: Mapped[ProductConfigurationRecord] = relationship(
        back_populates="pricing_rules"
    )


class ProductPriceRecord(Base):
    __tablename__ = "catalog_product_prices"
    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="ck_catalog_product_price_nonnegative"),
    )

    product_name: Mapped[str] = mapped_column(String(200), primary_key=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
