import unittest
from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import catalog.repositories.records
import inventory.repositories.inventory_repository
import sales.repositories.records
from catalog.models.brand import Brand
from catalog.models.category import Category
from catalog.models.product import Product
from catalog.models.product_configuration import ProductConfiguration
from catalog.repositories.category_repository import CategoryRepository
from catalog.repositories.configuration_repository import ConfigurationRepository
from catalog.repositories.pricing_repository import PricingRepository
from catalog.repositories.product_repository import ProductRepository
from inventory.models.inventory import InventoryLot
from inventory.repositories.inventory_repository import InventoryLotRecord, InventoryLotRepository
from sales.models.sales_order import Customer, SalesOrderStatus
from sales.repositories.sales_order_repository import SalesOrderRepository
from sales.services.sales_order_service import SalesOrderService
from shared.database import Base
from shared.pricing import Pricing, PricingRule


class SalesOrderTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.inventory_repo = InventoryLotRepository(self.session)
        self.sales_repo = SalesOrderRepository(self.session)
        self.service = SalesOrderService(
            self.sales_repo,
            self.inventory_repo,
            pricing_repository=PricingRepository(self.session),
            product_repository=ProductRepository(self.session),
        )
        self.customer = Customer(customer_id="C-1", name="Retailer")

        category = Category(name="Parts", specification_types=[])
        CategoryRepository(self.session).save_category(category)
        self.product = Product(
            product_id="P-1",
            name="Filter",
            description="Oil filter",
            brand=Brand(name="Acme", products=["P-1"]),
            category=category,
            configurations=[],
        )
        ProductRepository(self.session).add_product(self.product)
        self.configuration = ProductConfiguration(
            product=self.product,
            specifications=[],
            pricing=Pricing([
                PricingRule(1, 4, Decimal("5.00")),
                PricingRule(5, None, Decimal("4.00")),
            ]),
            material=None,
            weight=None,
            color=None,
            size=None,
            volume=None,
            length=None,
            width=None,
            unit=None,
            additional_features=None,
        )
        self.configuration_id = ConfigurationRepository(self.session).save_configuration(
            self.configuration
        )
        self.inventory_repo.save_inventory_lot(
            InventoryLot(
                id="LOT-1",
                product_configuration_id=str(self.configuration_id),
                warehouse_id="WH-1",
                received_at=datetime(2026, 1, 1),
                quantity=10,
                available_quantity=10,
            )
        )

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def create_order(self, quantity=3, **overrides):
        line = {"configuration_id": self.configuration_id, "quantity": quantity}
        line.update(overrides)
        return self.service.create_order(self.customer, "WH-1", [line])

    def test_create_order_resolves_price_from_quantity_tier(self):
        order = self.create_order(quantity=3)
        self.assertEqual(order.lines[0].unit_price, Decimal("5.00"))

        bulk_order = self.create_order(quantity=5)
        self.assertEqual(bulk_order.lines[0].unit_price, Decimal("4.00"))

    def test_create_order_accepts_explicit_price_and_rejects_invalid_input(self):
        order = self.create_order(quantity=2, unit_price="3.25")
        self.assertEqual(order.total, Decimal("6.50"))

        with self.assertRaisesRegex(ValueError, "positive integer"):
            self.create_order(quantity=0)
        with self.assertRaisesRegex(ValueError, "was not found"):
            self.service.create_order(
                self.customer,
                "WH-1",
                [{"configuration_id": 999, "quantity": 1}],
            )

    def test_payment_reserves_stock_and_fails_when_unavailable(self):
        order = self.create_order(quantity=6)
        self.service.confirm_payment(order.order_id)

        lot = self.session.get(InventoryLotRecord, "LOT-1")
        self.assertEqual(lot.available_quantity, 4)
        self.assertEqual(lot.reserved_quantity, 6)

        too_large = self.create_order(quantity=9)
        with self.assertRaisesRegex(ValueError, "Insufficient stock"):
            self.service.confirm_payment(too_large.order_id)
        self.assertEqual(
            self.service.get_order(too_large.order_id).status,
            SalesOrderStatus.CREATED,
        )

    def test_full_lifecycle_dispatches_reserved_stock(self):
        order = self.create_order(quantity=2)
        order_id = order.order_id

        self.service.confirm_payment(order_id)
        self.service.start_picking(order_id)
        self.service.record_fulfillment(order_id, self.configuration_id, 2)
        self.service.mark_packed(order_id)
        self.service.dispatch(order_id)
        self.service.mark_delivered(order_id)
        completed = self.service.complete(order_id)

        self.assertEqual(completed.status, SalesOrderStatus.COMPLETED)
        lot = self.session.get(InventoryLotRecord, "LOT-1")
        self.assertEqual(lot.quantity, 8)
        self.assertEqual(lot.reserved_quantity, 0)

    def test_cancelling_a_paid_order_releases_reservation(self):
        order = self.create_order(quantity=4)
        self.service.confirm_payment(order.order_id)
        cancelled = self.service.cancel(order.order_id)

        self.assertEqual(cancelled.status, SalesOrderStatus.CANCELLED)
        lot = self.session.get(InventoryLotRecord, "LOT-1")
        self.assertEqual(lot.available_quantity, 10)
        self.assertEqual(lot.reserved_quantity, 0)

    def test_invalid_lifecycle_transition_is_rejected(self):
        order = self.create_order(quantity=1)

        with self.assertRaisesRegex(ValueError, "Cannot move sales order"):
            self.service.start_picking(order.order_id)


if __name__ == "__main__":
    unittest.main()
