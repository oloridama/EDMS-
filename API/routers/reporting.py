from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from API.dependencies import get_session, require_permission
from authentication.models.user import REPORTING_READ
from reporting.repositories.reporting_repository import ReportingRepository
from reporting.services.reporting_service import ReportingService

router = APIRouter(prefix="/reports", tags=["reporting"])


def build_service(session: Session) -> ReportingService:
    return ReportingService(ReportingRepository(session))


@router.get("/inventory")
def inventory_levels(
    session: Session = Depends(get_session),
    _=Depends(require_permission(REPORTING_READ)),
):
    return [asdict(item) for item in build_service(session).inventory_levels()]


@router.get("/sales")
def sales_summary(
    session: Session = Depends(get_session),
    _=Depends(require_permission(REPORTING_READ)),
):
    return [asdict(item) for item in build_service(session).sales_summary()]


@router.get("/procurement")
def procurement_summary(
    session: Session = Depends(get_session),
    _=Depends(require_permission(REPORTING_READ)),
):
    return [asdict(item) for item in build_service(session).procurement_summary()]


@router.get("/stock-movements")
def stock_movement_summary(
    session: Session = Depends(get_session),
    _=Depends(require_permission(REPORTING_READ)),
):
    return [asdict(item) for item in build_service(session).stock_movement_summary()]
