from inventory.models.inventory import InventoryLot
from inventory.repositories.inventory_repository import InventoryLotRepository
from sqlalchemy.orm import Session


class InventoryService:
    def __init__(self, db_session: Session):
        self.repository = InventoryLotRepository(db_session)

    def save_lot(self, lot: InventoryLot) -> str:
        return self.repository.save_inventory_lot(lot)

    def get_lot(self, lot_id: str) -> InventoryLot | None:
        record = self.repository.get_inventory_lot(lot_id)
        if record is None:
            return None
        return self.repository.from_record(record)

    def get_available_stock(self, product_configuration_id: str, warehouse_id: str) -> int:
        return self.repository.get_available_stock(product_configuration_id, warehouse_id)
