from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from API.dependencies import get_session, require_permission
from API.schemas import (
    CustomerIn,
    FulfillRequest,
    SalesLineResponse,
    SalesOrderCreate,
    SalesOrderResponse,
)
from authentication.models.user import SALES_READ, SALES_WRITE
from catalog.repositories.pricing_repository import PricingRepository
from catalog.repositories.product_repository import ProductRepository
from inventory.repositories.inventory_repository import InventoryLotRepository
from sales.models.sales_order import Customer, SalesOrder
from sales.repositories.sales_order_repository import SalesOrderRepository
from sales.services.sales_order_service import SalesOrderService

router = APIRouter(prefix="/sales", tags=["sales"])


def to_response(order: SalesOrder) -> SalesOrderResponse:
    return SalesOrderResponse(
        order_id=order.order_id,
        customer_id=order.customer.customer_id,
        warehouse_id=order.warehouse_id,
        status=order.status.value,
        total=order.total,
        lines=[
            SalesLineResponse(
                configuration_id=line.configuration_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                fulfilled_quantity=line.fulfilled_quantity,
                dispatched_quantity=line.dispatched_quantity,
            )
            for line in order.lines
        ],
    )


def build_service(session: Session) -> SalesOrderService:
    return SalesOrderService(
        SalesOrderRepository(session),
        InventoryLotRepository(session),
        pricing_repository=PricingRepository(session),
        product_repository=ProductRepository(session),
    )


@router.post("/orders", response_model=SalesOrderResponse, status_code=201)
def create_order(
    payload: SalesOrderCreate,
    session: Session = Depends(get_session),
    _=Depends(require_permission(SALES_WRITE)),
):
    order = build_service(session).create_order(
        Customer(**payload.customer.model_dump()),
        payload.warehouse_id,
        [line.model_dump() for line in payload.lines],
    )
    return to_response(order)


@router.get("/orders/{order_id}", response_model=SalesOrderResponse)
def get_order(
    order_id: int,
    session: Session = Depends(get_session),
    _=Depends(require_permission(SALES_READ)),
):
    order = build_service(session).get_order(order_id)
    if order is None:
        raise HTTPException(404, f"Sales order {order_id} was not found.")
    return to_response(order)


@router.post("/orders/{order_id}/pay", response_model=SalesOrderResponse)
def pay_order(
    order_id: int,
    session: Session = Depends(get_session),
    _=Depends(require_permission(SALES_WRITE)),
):
    return to_response(build_service(session).confirm_payment(order_id))


@router.post("/orders/{order_id}/pick", response_model=SalesOrderResponse)
def pick_order(
    order_id: int,
    session: Session = Depends(get_session),
    _=Depends(require_permission(SALES_WRITE)),
):
    return to_response(build_service(session).start_picking(order_id))


@router.post("/orders/{order_id}/fulfill", response_model=SalesOrderResponse)
def fulfill_order(
    order_id: int,
    payload: FulfillRequest,
    session: Session = Depends(get_session),
    _=Depends(require_permission(SALES_WRITE)),
):
    return to_response(
        build_service(session).record_fulfillment(
            order_id,
            payload.configuration_id,
            payload.quantity,
        )
    )


@router.post("/orders/{order_id}/pack", response_model=SalesOrderResponse)
def pack_order(
    order_id: int,
    session: Session = Depends(get_session),
    _=Depends(require_permission(SALES_WRITE)),
):
    return to_response(build_service(session).mark_packed(order_id))


@router.post("/orders/{order_id}/dispatch", response_model=SalesOrderResponse)
def dispatch_order(
    order_id: int,
    session: Session = Depends(get_session),
    _=Depends(require_permission(SALES_WRITE)),
):
    return to_response(build_service(session).dispatch(order_id))


@router.post("/orders/{order_id}/deliver", response_model=SalesOrderResponse)
def deliver_order(
    order_id: int,
    session: Session = Depends(get_session),
    _=Depends(require_permission(SALES_WRITE)),
):
    return to_response(build_service(session).mark_delivered(order_id))


@router.post("/orders/{order_id}/complete", response_model=SalesOrderResponse)
def complete_order(
    order_id: int,
    session: Session = Depends(get_session),
    _=Depends(require_permission(SALES_WRITE)),
):
    return to_response(build_service(session).complete(order_id))


@router.post("/orders/{order_id}/cancel", response_model=SalesOrderResponse)
def cancel_order(
    order_id: int,
    session: Session = Depends(get_session),
    _=Depends(require_permission(SALES_WRITE)),
):
    return to_response(build_service(session).cancel(order_id))
