from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from catalog.models.product import Product
from catalog.repositories.mappers import product_from_record
from catalog.repositories.records import CategoryRecord, ProductRecord
from shared.logging import log


class ProductRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def add_product(self, product: Product) -> str:
        category = self.db_session.scalar(
            select(CategoryRecord).where(CategoryRecord.name == product.category.name)
        )
        if category is None:
            raise ValueError(f"Category '{product.category.name}' was not found.")

        existing = self.db_session.get(ProductRecord, product.product_id)
        if existing is not None:
            raise ValueError(f"Product '{product.product_id}' already exists.")

        record = ProductRecord(
            product_id=product.product_id,
            name=product.name,
            description=product.description,
            brand_name=product.brand.name,
            category_id=category.id,
        )
        self.db_session.add(record)
        self.db_session.flush()
        return record.product_id

    def get_product(self, product_id: str) -> Product | None:
        record = self.db_session.scalar(
            select(ProductRecord)
            .options(
                selectinload(ProductRecord.category).selectinload(
                    CategoryRecord.specification_types
                ),
                selectinload(ProductRecord.configurations),
            )
            .where(ProductRecord.product_id == product_id)
        )
        return product_from_record(record) if record else None

    def get_product_by_name(self, product_name: str) -> Product | None:
        record = self.db_session.scalar(
            select(ProductRecord)
            .options(
                selectinload(ProductRecord.category).selectinload(
                    CategoryRecord.specification_types
                ),
                selectinload(ProductRecord.configurations),
            )
            .where(ProductRecord.name == product_name)
            .order_by(ProductRecord.product_id)
        )
        return product_from_record(record) if record else None

    def remove_product(self, product_name: str) -> None:
        record = self.db_session.scalar(
            select(ProductRecord).where(ProductRecord.name == product_name)
        )
        if record is None:
            raise ValueError(f"Product '{product_name}' was not found.")
        self.db_session.delete(record)
        self.db_session.flush()
        log.info(f"Product {product_name} removed from catalog")

    def check_product_unit_price(
        self,
        product_name: str,
        quantity: int = 1,
    ) -> Decimal | None:
        product = self.get_product_by_name(product_name)
        if product is None:
            return None

        matching_prices = [
            rule.unit_price
            for configuration in product.configurations
            for rule in configuration.pricing.pricing_rules
            if (rule.min_quantity is None or quantity >= rule.min_quantity)
            and (rule.max_quantity is None or quantity <= rule.max_quantity)
        ]
        if len(matching_prices) > 1:
            raise ValueError(
                f"Multiple pricing tiers match '{product_name}' at quantity {quantity}."
            )
        return matching_prices[0] if matching_prices else None
