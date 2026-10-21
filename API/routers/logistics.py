from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from API.dependencies import get_session, require_permission
from API.schemas import (
    ShipmentCreate,
    ShipmentResponse,
    ShipmentStatusUpdate,
    TransporterCreate,
)
from authentication.models.user import LOGISTICS_READ, LOGISTICS_WRITE
from catalog.repositories.configuration_repository import ConfigurationRepository
from logistics.models.logistic import Logistic, LogisticStatus
from logistics.models.mode_of_transport import Dimensions, ModeOfTransport
from logistics.models.transporter import Transporter
from logistics.repositories.logistic_repository import LogisticRepository
from logistics.repositories.transporter_repository import TransporterRepository
from logistics.services.logistic_service import LogisticService

router = APIRouter(prefix="/logistics", tags=["logistics"])


def to_response(ticket: Logistic, configuration_ids: list[int]) -> ShipmentResponse:
    return ShipmentResponse(
        tracking_id=ticket.tracking_id,
        eta=ticket.eta,
        status=ticket.status.value,
        transporter_id=ticket.transporter_id,
        transporter_name=ticket.transporter_name_at_dispatch,
        mode=ticket.mode_of_transportation.name,
        configuration_ids=configuration_ids,
    )


@router.post("/transporters", status_code=201)
def create_transporter(
    payload: TransporterCreate,
    session: Session = Depends(get_session),
    _=Depends(require_permission(LOGISTICS_WRITE)),
):
    transporter = Transporter(
        name=payload.name,
        contact_number=payload.contact_number,
        email=payload.email,
        address=payload.address,
        transportation_type=payload.transportation_type,
        marital_status=payload.marital_status,
        dob=payload.dob,
        citizenship=payload.citizenship,
    )
    transporter_id = TransporterRepository(session).save(transporter)
    return {"transporter_id": transporter_id}


@router.post("/shipments", response_model=ShipmentResponse, status_code=201)
def create_shipment(
    payload: ShipmentCreate,
    session: Session = Depends(get_session),
    _=Depends(require_permission(LOGISTICS_WRITE)),
):
    configurations = ConfigurationRepository(session)
    package = []
    for configuration_id in payload.configuration_ids:
        configuration = configurations.get_configuration(configuration_id)
        if configuration is None:
            raise HTTPException(
                404,
                f"Product configuration {configuration_id} was not found.",
            )
        package.append(configuration)

    mode = payload.mode_of_transport
    service = LogisticService(LogisticRepository(session))
    ticket = service.create_logistic_ticket(
        tracking_id=payload.tracking_id,
        eta_text=payload.eta.isoformat() if payload.eta else None,
        package=package,
        transporter_id=payload.transporter_id,
        transporter_name=payload.transporter_name,
        mode_of_transport=ModeOfTransport(
            name=mode.name,
            description=Dimensions(mode.length, mode.width, mode.height),
            reg_no=mode.reg_no,
        ),
    )
    return to_response(ticket, payload.configuration_ids)


@router.get("/shipments/{tracking_id}", response_model=ShipmentResponse)
def get_shipment(
    tracking_id: str,
    session: Session = Depends(get_session),
    _=Depends(require_permission(LOGISTICS_READ)),
):
    ticket = LogisticRepository(session).fetch_ticket_by_id(tracking_id)
    if ticket is None:
        raise HTTPException(404, f"Shipment '{tracking_id}' was not found.")
    configuration_ids = LogisticRepository(session).get_package_configuration_ids(
        tracking_id
    )
    return to_response(ticket, configuration_ids)


@router.patch("/shipments/{tracking_id}/status", response_model=ShipmentResponse)
def update_shipment_status(
    tracking_id: str,
    payload: ShipmentStatusUpdate,
    session: Session = Depends(get_session),
    _=Depends(require_permission(LOGISTICS_WRITE)),
):
    service = LogisticService(LogisticRepository(session))
    ticket = service.update_logistic_status(
        LogisticStatus(payload.status),
        tracking_id,
    )
    configuration_ids = LogisticRepository(session).get_package_configuration_ids(
        tracking_id
    )
    return to_response(ticket, configuration_ids)
