from reporting.models.report import (
    InventoryLevelReport,
    ProcurementSummaryReport,
    SalesSummaryReport,
    StockMovementSummaryReport,
)
from reporting.repositories.reporting_repository import ReportingRepository


class ReportingService:
    """Expose operational reports without duplicating persistence logic."""

    def __init__(self, reporting_repository: ReportingRepository):
        self.reporting_repository = reporting_repository

    def inventory_levels(self) -> list[InventoryLevelReport]:
        return self.reporting_repository.inventory_levels()

    def sales_summary(self) -> list[SalesSummaryReport]:
        return self.reporting_repository.sales_summary()

    def procurement_summary(self) -> list[ProcurementSummaryReport]:
        return self.reporting_repository.procurement_summary()

    def stock_movement_summary(self) -> list[StockMovementSummaryReport]:
        return self.reporting_repository.stock_movement_summary()
