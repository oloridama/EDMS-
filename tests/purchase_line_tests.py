import unittest
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from procurement.models.purchase_line import PurchaseLine
from procurement.models.purchase_order import PurchaseOrder
from procurement.models.supplier import Supplier
from procurement.repositories.purchase_order_repository import (
    PurchaseOrderLineRecord,
    PurchaseOrderRecord,
    PurchaseOrderRepository,
)
from procurement.services.purchase_line_service import PurchaseLineService
from procurement.services.purchase_order_service import PurchaseOrderService
from shared.database import Base


class PurchaseLineRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.repository = PurchaseOrderRepository(self.session)
        self.service = PurchaseLineService(self.repository)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def add_order(self, order_id, product_names):
        order = PurchaseOrderRecord(
            id=order_id,
            supplier_name="Acme",
            status="draft",
            total=0,
            lines=[
                PurchaseOrderLineRecord(
                    product_name=name,
                    product_id=f"SKU-{name}",
                    quantity=3,
                    received_quantity=0,
                    manufacturer_name="Acme",
                    unit_price=4.50,
                )
                for name in product_names
            ],
        )
        self.session.add(order)
        self.session.flush()
        return order

    def test_get_purchase_line_queries_the_order_repository(self):
        order = self.add_order(42, ["Widget", "Gadget"])

        result = self.service.get_purchase_line(42, "SKU-Widget")

        self.assertIsInstance(result, PurchaseOrderLineRecord)
        self.assertEqual(result.purchase_order_id, order.id)
        self.assertEqual(result.product_name, "Widget")

    def test_get_purchase_line_distinguishes_missing_order_and_product(self):
        self.add_order(42, ["Widget"])

        with self.assertRaisesRegex(ValueError, "Purchase order 99"):
            self.service.get_purchase_line(99, "SKU-Widget")

        with self.assertRaisesRegex(ValueError, "Purchase line for product"):
            self.service.get_purchase_line(42, "SKU-Missing")

    def test_purchase_order_rejects_duplicate_product_lines(self):
        def line(product_id):
            product = SimpleNamespace(product_id=product_id)
            configuration = SimpleNamespace(product=product)
            return PurchaseLine(
                product=configuration,
                quantity=1,
                manufacturer=SimpleNamespace(name="Acme"),
                unit_price=Decimal("2.00"),
            )

        with self.assertRaisesRegex(ValueError, "duplicate products"):
            PurchaseOrder(
                supplier=Supplier("Acme", "Address", "a@example.com", "555"),
                purchase_lines=[line("SKU-1"), line("SKU-1")],
            )

    def test_database_rejects_duplicate_product_lines(self):
        order = PurchaseOrderRecord(
            supplier_name="Acme",
            status="draft",
            total=4,
            lines=[
                PurchaseOrderLineRecord(
                    product_id="SKU-1",
                    product_name="Widget",
                    quantity=1,
                    received_quantity=0,
                    manufacturer_name="Acme",
                    unit_price=2,
                ),
                PurchaseOrderLineRecord(
                    product_id="SKU-1",
                    product_name="Widget",
                    quantity=1,
                    received_quantity=0,
                    manufacturer_name="Acme",
                    unit_price=2,
                ),
            ],
        )
        self.session.add(order)

        with self.assertRaises(IntegrityError):
            self.session.flush()

        self.session.rollback()

    def test_database_rejects_invalid_line_quantities_and_prices(self):
        order = PurchaseOrderRecord(
            supplier_name="Acme",
            status="draft",
            total=0,
        )
        self.session.add(order)
        self.session.flush()

        invalid_line = PurchaseOrderLineRecord(
            purchase_order_id=order.id,
            product_id="SKU-1",
            product_name="Widget",
            quantity=1,
            received_quantity=2,
            manufacturer_name="Acme",
            unit_price=2,
        )
        self.session.add(invalid_line)

        with self.assertRaises(IntegrityError):
            self.session.flush()

        self.session.rollback()

    def test_save_preserves_order_time_snapshots(self):
        supplier = Supplier("Supplier at order time", "Address", "a@example.com", "555")
        product = SimpleNamespace(product_id="SKU-1", name="Widget at order time")
        configuration = SimpleNamespace(product=product)
        manufacturer = SimpleNamespace(name="Manufacturer at order time")
        line = PurchaseLine(
            product=configuration,
            quantity=2,
            manufacturer=manufacturer,
            unit_price=Decimal("4.25"),
        )
        order = PurchaseOrder(supplier=supplier, purchase_lines=[line])

        self.repository.save_purchase_order(order)
        supplier.name = "Renamed supplier"
        product.name = "Renamed product"
        manufacturer.name = "Renamed manufacturer"
        line.unit_price = Decimal("9.99")

        saved_order = self.repository.get_purchase_order(order.id)
        saved_line = self.service.get_purchase_line(order.id, "SKU-1")

        self.assertEqual(saved_order.supplier_name, "Supplier at order time")
        self.assertEqual(saved_order.total, Decimal("8.50"))
        self.assertEqual(saved_line.product_name, "Widget at order time")
        self.assertEqual(saved_line.manufacturer_name, "Manufacturer at order time")
        self.assertEqual(saved_line.unit_price, Decimal("4.25"))

    def test_purchase_order_status_updates_follow_lifecycle(self):
        order = self.add_order(84, ["Widget"])
        service = PurchaseOrderService(self.service, self.repository)

        updated = service.update_purchase_order(84, {"status": "approved"})
        self.assertEqual(updated.status, "approved")

        updated = service.update_purchase_order(84, {"status": "sent"})
        self.assertEqual(updated.status, "sent")

    def test_purchase_order_status_update_rejects_invalid_transition_and_fields(self):
        self.add_order(85, ["Widget"])
        service = PurchaseOrderService(self.service, self.repository)

        with self.assertRaisesRegex(ValueError, "transition"):
            service.update_purchase_order(85, {"status": "completed"})

        with self.assertRaisesRegex(ValueError, "Unsupported"):
            service.update_purchase_order(85, {"supplier_name": "Changed"})

    def test_purchase_order_status_update_rejects_missing_order(self):
        service = PurchaseOrderService(self.service, self.repository)

        with self.assertRaisesRegex(ValueError, "Purchase order 999"):
            service.update_purchase_order(999, {"status": "approved"})

    def test_partial_receipt_status_requires_matching_received_quantities(self):
        order = self.add_order(86, ["Widget"])
        service = PurchaseOrderService(self.service, self.repository)
        order.status = "sent"

        with self.assertRaisesRegex(ValueError, "some, but not all"):
            service.update_purchase_order(86, {"status": "partially_received"})

        order.lines[0].received_quantity = 1
        self.session.flush()
        updated = service.update_purchase_order(86, {"status": "partially_received"})
        self.assertEqual(updated.status, "partially_received")

        updated = service.update_purchase_order(86, {"status": "completed"})
        self.assertEqual(updated.status, "completed")


if __name__ == "__main__":
    unittest.main()
