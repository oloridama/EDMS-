from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from API.dependencies import get_session, require_permission
from API.schemas import (
    PurchaseLineResponse,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    StatusUpdate,
)
from authentication.models.user import PROCUREMENT_READ, PROCUREMENT_WRITE
from catalog.repositories.configuration_repository import ConfigurationRepository
from procurement.models.manufacturer import Manufacturer
from procurement.models.supplier import Supplier
from procurement.repositories.purchase_order_repository import (
    PurchaseOrderRecord,
    PurchaseOrderRepository,
)
from procurement.services.purchase_line_service import PurchaseLineService
from procurement.services.purchase_order_service import PurchaseOrderService

router = APIRouter(prefix="/procurement", tags=["procurement"])


def to_response(record: PurchaseOrderRecord) -> PurchaseOrderResponse:
    return PurchaseOrderResponse(
        order_id=record.id,
        supplier_name=record.supplier_name,
        status=record.status,
        total=record.total,
        lines=[
            PurchaseLineResponse(
                product_id=line.product_id,
                product_name=line.product_name,
                quantity=line.quantity,
                received_quantity=line.received_quantity,
                manufacturer_name=line.manufacturer_name,
                unit_price=line.unit_price,
            )
            for line in record.lines
        ],
    )


def build_service(session: Session) -> PurchaseOrderService:
    repository = PurchaseOrderRepository(session)
    return PurchaseOrderService(PurchaseLineService(repository), repository)


@router.post("/orders", response_model=PurchaseOrderResponse, status_code=201)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    session: Session = Depends(get_session),
    _=Depends(require_permission(PROCUREMENT_WRITE)),
):
    configurations = ConfigurationRepository(session)
    lines = []
    for line in payload.lines:
        configuration = configurations.get_configuration(line.configuration_id)
        if configuration is None:
            raise HTTPException(
                404,
                f"Product configuration {line.configuration_id} was not found.",
            )
        lines.append(
            {
                "product_configuration": configuration,
                "quantity": line.quantity,
                "manufacturer": Manufacturer(name=line.manufacturer_name),
                "unit_price": line.unit_price,
            }
        )

    order = build_service(session).create_purchase_order(
        {
            "supplier": Supplier(**payload.supplier.model_dump()),
            "purchase_lines": lines,
        }
    )
    return to_response(PurchaseOrderRepository(session).get_purchase_order(order.id))


@router.get("/orders/{order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    order_id: int,
    session: Session = Depends(get_session),
    _=Depends(require_permission(PROCUREMENT_READ)),
):
    record = PurchaseOrderRepository(session).get_purchase_order(order_id)
    if record is None:
        raise HTTPException(404, f"Purchase order {order_id} was not found.")
    return to_response(record)


@router.patch("/orders/{order_id}/status", response_model=PurchaseOrderResponse)
def update_status(
    order_id: int,
    payload: StatusUpdate,
    session: Session = Depends(get_session),
    _=Depends(require_permission(PROCUREMENT_WRITE)),
):
    build_service(session).update_purchase_order(order_id, {"status": payload.status})
    record = PurchaseOrderRepository(session).get_purchase_order(order_id)
    return to_response(record)
