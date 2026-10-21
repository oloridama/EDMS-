from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from catalog.repositories.records import ProductPriceRecord
from shared.logging import log


class PricingRepository:
    """Persist product-level fallback prices in the catalog database."""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def save_price(self, product: str, price: Decimal | int | str) -> None:
        price_value = Decimal(str(price))
        if price_value < 0:
            raise ValueError("Product price cannot be negative.")
        record = self.db_session.get(ProductPriceRecord, product)
        if record is None:
            record = ProductPriceRecord(product_name=product, unit_price=price_value)
            self.db_session.add(record)
        else:
            record.unit_price = price_value
        self.db_session.flush()

    def edit_price(self, product: str, amount: Decimal | int | str) -> None:
        record = self.db_session.get(ProductPriceRecord, product)
        if record is None:
            raise ValueError(f"No price is recorded for '{product}'.")
        price_value = Decimal(str(amount))
        if price_value < 0:
            raise ValueError("Product price cannot be negative.")
        old_price = record.unit_price
        record.unit_price = price_value
        self.db_session.flush()
        log(f"{product} price changed from {old_price} to {price_value}.")

    def get_price(self, product: str) -> Decimal | None:
        return self.db_session.scalar(
            select(ProductPriceRecord.unit_price).where(
                ProductPriceRecord.product_name == product
            )
        )

    @staticmethod
    def total(unit_price: Decimal, quantity: int) -> Decimal:
        if quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        return unit_price * quantity
