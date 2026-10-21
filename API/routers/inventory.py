from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from API.dependencies import get_session, require_permission
from API.schemas import LotCreate, LotResponse
from authentication.models.user import INVENTORY_READ, INVENTORY_WRITE
from inventory.models.inventory import InventoryLot
from inventory.repositories.inventory_repository import InventoryLotRepository
from inventory.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/lots", response_model=LotResponse, status_code=201)
def receive_lot(
    payload: LotCreate,
    session: Session = Depends(get_session),
    _=Depends(require_permission(INVENTORY_WRITE)),
):
    lot = InventoryLot(
        id=payload.lot_id,
        product_configuration_id=str(payload.configuration_id),
        warehouse_id=payload.warehouse_id,
        expiry_date=payload.expiry_date,
    )
    lot.receive(payload.quantity)
    InventoryService(session).save_lot(lot)
    return LotResponse(
        id=lot.id,
        configuration_id=lot.product_configuration_id,
        warehouse_id=lot.warehouse_id,
        quantity=lot.quantity,
        available_quantity=lot.available_quantity,
        reserved_quantity=lot.reserved_quantity,
        damaged_quantity=lot.damaged_quantity,
        expired_quantity=lot.expired_quantity,
    )


@router.get("/lots/{lot_id}", response_model=LotResponse)
def get_lot(
    lot_id: str,
    session: Session = Depends(get_session),
    _=Depends(require_permission(INVENTORY_READ)),
):
    lot = InventoryService(session).get_lot(lot_id)
    if lot is None:
        raise HTTPException(404, f"Inventory lot '{lot_id}' was not found.")
    return LotResponse(
        id=lot.id,
        configuration_id=lot.product_configuration_id,
        warehouse_id=lot.warehouse_id,
        quantity=lot.quantity,
        available_quantity=lot.available_quantity,
        reserved_quantity=lot.reserved_quantity,
        damaged_quantity=lot.damaged_quantity,
        expired_quantity=lot.expired_quantity,
    )


@router.get("/stock/{configuration_id}")
def get_stock(
    configuration_id: int,
    warehouse_id: str,
    session: Session = Depends(get_session),
    _=Depends(require_permission(INVENTORY_READ)),
):
    available = InventoryLotRepository(session).get_available_stock(
        str(configuration_id),
        warehouse_id,
    )
    return {
        "configuration_id": configuration_id,
        "warehouse_id": warehouse_id,
        "available_quantity": available,
    }
