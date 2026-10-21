import unittest
from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import catalog.repositories.records
import inventory.repositories.inventory_repository
import procurement.repositories.purchase_order_repository
import sales.repositories.records
from catalog.models.brand import Brand
from catalog.models.category import Category
from catalog.models.product import Product
from catalog.models.product_configuration import ProductConfiguration
from catalog.repositories.category_repository import CategoryRepository
from catalog.repositories.configuration_repository import ConfigurationRepository
from catalog.repositories.product_repository import ProductRepository
from inventory.models.inventory import InventoryLot
from inventory.repositories.inventory_repository import InventoryLotRepository
from procurement.repositories.purchase_order_repository import (
    PurchaseOrderLineRecord,
    PurchaseOrderRecord,
)
from reporting.repositories.reporting_repository import ReportingRepository
from reporting.services.reporting_service import ReportingService
from sales.models.sales_order import Customer, SalesOrder, SalesOrderLine
from sales.repositories.sales_order_repository import SalesOrderRepository
from shared.database import Base
from shared.pricing import Pricing, PricingRule


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

        category = Category(name="Parts", specification_types=[])
        CategoryRepository(self.session).save_category(category)
        product = Product(
            product_id="P-1",
            name="Filter",
            description="Oil filter",
            brand=Brand(name="Acme", products=["P-1"]),
            category=category,
            configurations=[],
        )
        ProductRepository(self.session).add_product(product)
        configuration = ProductConfiguration(
            product=product,
            specifications=[],
            pricing=Pricing([PricingRule(1, None, Decimal("5.00"))]),
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
            configuration
        )

        receipt_lot = InventoryLot(
            id="LOT-1",
            product_configuration_id=str(self.configuration_id),
            warehouse_id="WH-1",
            received_at=datetime(2026, 1, 1),
        )
        receipt_lot.receive(10)
        InventoryLotRepository(self.session).save_inventory_lot(receipt_lot)

        sales_repo = SalesOrderRepository(self.session)
        order = SalesOrder(
            Customer(customer_id="C-1", name="Retailer"),
            "WH-1",
            [
                SalesOrderLine(
                    product_configuration=configuration,
                    configuration_id=self.configuration_id,
                    quantity=2,
                    unit_price=Decimal("5.00"),
                )
            ],
        )
        sales_repo.save_order(order)

        purchase_order = PurchaseOrderRecord(
            supplier_name="Acme",
            status="sent",
            total=Decimal("20.00"),
            lines=[
                PurchaseOrderLineRecord(
                    product_id="SKU-1",
                    product_name="Filter",
                    quantity=4,
                    received_quantity=2,
                    manufacturer_name="Acme",
                    unit_price=Decimal("5.00"),
                )
            ],
        )
        self.session.add(purchase_order)
        self.session.flush()

        self.service = ReportingService(ReportingRepository(self.session))

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_inventory_levels_report(self):
        report = self.service.inventory_levels()
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0].available_quantity, 10)
        self.assertEqual(report[0].warehouse_id, "WH-1")

    def test_sales_summary_report(self):
        report = self.service.sales_summary()
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0].status, "created")
        self.assertEqual(report[0].order_count, 1)
        self.assertEqual(report[0].total_value, Decimal("10.00"))

    def test_procurement_summary_report(self):
        report = self.service.procurement_summary()
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0].status, "sent")
        self.assertEqual(report[0].ordered_quantity, 4)
        self.assertEqual(report[0].received_quantity, 2)
        self.assertEqual(report[0].total_value, Decimal("20.00"))

    def test_stock_movement_summary_report(self):
        report = self.service.stock_movement_summary()
        movement_types = {item.movement_type: item for item in report}
        self.assertIn("receipt", movement_types)
        self.assertEqual(movement_types["receipt"].total_quantity, 10)


if __name__ == "__main__":
    unittest.main()
