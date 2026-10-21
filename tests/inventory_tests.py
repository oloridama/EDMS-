from datetime import date, datetime

import unittest

from inventory.models.inventory import InventoryLot, StockMovementType
from inventory.repositories.inventory_repository import InventoryLotRepository
from shared.database import Base, Database


class InventoryLotTests(unittest.TestCase):
    def test_receive_and_reserve_update_balances(self):
        lot = InventoryLot(
            id="LOT-001",
            product_configuration_id="CFG-100",
            warehouse_id="WH-1",
            received_at=datetime(2026, 1, 10),
            expiry_date=date(2026, 12, 31),
            quantity=10,
            available_quantity=10,
        )

        lot.reserve(3)
        self.assertEqual(lot.available_quantity, 7)
        self.assertEqual(lot.reserved_quantity, 3)

        lot.receive(2)
        self.assertEqual(lot.available_quantity, 9)
        self.assertEqual(lot.quantity, 12)

    def test_reserve_rejects_insufficient_available_quantity(self):
        lot = InventoryLot(
            id="LOT-002",
            product_configuration_id="CFG-100",
            warehouse_id="WH-1",
            received_at=datetime(2026, 1, 10),
            quantity=5,
            available_quantity=5,
        )

        with self.assertRaisesRegex(ValueError, "available"):
            lot.reserve(6)

    def test_damage_and_expiry_move_inventory_out_of_available_stock(self):
        lot = InventoryLot(
            id="LOT-003",
            product_configuration_id="CFG-200",
            warehouse_id="WH-1",
            received_at=datetime(2026, 1, 10),
            quantity=20,
            available_quantity=20,
        )

        lot.mark_damaged(4)
        lot.mark_expired(3)

        self.assertEqual(lot.available_quantity, 13)
        self.assertEqual(lot.damaged_quantity, 4)
        self.assertEqual(lot.expired_quantity, 3)
        self.assertEqual(lot.total_quantity, 20)

    def test_stock_movement_type_is_tracked(self):
        movement = lot = InventoryLot(
            id="LOT-004",
            product_configuration_id="CFG-300",
            warehouse_id="WH-1",
            received_at=datetime(2026, 1, 10),
            quantity=10,
            available_quantity=10,
        ).record_movement(
            movement_type=StockMovementType.RECEIPT,
            quantity=10,
            reference_id="PO-123",
            note="Initial receipt",
        )

        self.assertEqual(movement.movement_type, StockMovementType.RECEIPT)
        self.assertEqual(movement.quantity, 10)


class InventoryRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.database = Database("sqlite:///:memory:")
        Base.metadata.create_all(self.database.engine)
        self.session = self.database._session_factory()
        self.repository = InventoryLotRepository(self.session)

    def tearDown(self):
        self.session.close()

    def test_repository_saves_and_loads_inventory_lot(self):
        lot = InventoryLot(
            id="LOT-DB-1",
            product_configuration_id="CFG-500",
            warehouse_id="WH-2",
            received_at=datetime(2026, 2, 1),
            expiry_date=date(2026, 12, 31),
            quantity=15,
            available_quantity=15,
        )
        lot.record_movement(
            movement_type=StockMovementType.RECEIPT,
            quantity=15,
            reference_id="PO-700",
            note="Initial purchase",
        )

        saved_lot_id = self.repository.save_inventory_lot(lot)
        persisted = self.repository.get_inventory_lot(saved_lot_id)

        self.assertEqual(saved_lot_id, "LOT-DB-1")
        self.assertEqual(persisted.product_configuration_id, "CFG-500")
        self.assertEqual(persisted.available_quantity, 15)
        self.assertEqual(len(persisted.movements), 1)
        self.assertEqual(persisted.movements[0].movement_type, "receipt")


if __name__ == "__main__":
    unittest.main()
