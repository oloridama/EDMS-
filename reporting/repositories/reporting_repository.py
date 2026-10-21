from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from inventory.repositories.inventory_repository import (
    InventoryLotRecord,
    InventoryMovementRecord,
)
from procurement.repositories.purchase_order_repository import (
    PurchaseOrderLineRecord,
    PurchaseOrderRecord,
)
from reporting.models.report import (
    InventoryLevelReport,
    ProcurementSummaryReport,
    SalesSummaryReport,
    StockMovementSummaryReport,
)
from sales.repositories.records import SalesOrderRecord


class ReportingRepository:
    """Read-only aggregate queries for operational and management reporting."""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def inventory_levels(self) -> list[InventoryLevelReport]:
        rows = self.db_session.execute(
            select(
                InventoryLotRecord.product_configuration_id,
                InventoryLotRecord.warehouse_id,
                func.sum(InventoryLotRecord.available_quantity),
                func.sum(InventoryLotRecord.reserved_quantity),
                func.sum(InventoryLotRecord.damaged_quantity),
                func.sum(InventoryLotRecord.expired_quantity),
            )
            .group_by(
                InventoryLotRecord.product_configuration_id,
                InventoryLotRecord.warehouse_id,
            )
            .order_by(
                InventoryLotRecord.product_configuration_id,
                InventoryLotRecord.warehouse_id,
            )
        ).all()
        return [
            InventoryLevelReport(
                product_configuration_id=row[0],
                warehouse_id=row[1],
                available_quantity=int(row[2] or 0),
                reserved_quantity=int(row[3] or 0),
                damaged_quantity=int(row[4] or 0),
                expired_quantity=int(row[5] or 0),
            )
            for row in rows
        ]

    def sales_summary(self) -> list[SalesSummaryReport]:
        rows = self.db_session.execute(
            select(
                SalesOrderRecord.status,
                func.count(SalesOrderRecord.id),
                func.sum(SalesOrderRecord.total),
            )
            .group_by(SalesOrderRecord.status)
            .order_by(SalesOrderRecord.status)
        ).all()
        return [
            SalesSummaryReport(
                status=row[0],
                order_count=int(row[1] or 0),
                total_value=Decimal(row[2] or 0),
            )
            for row in rows
        ]

    def procurement_summary(self) -> list[ProcurementSummaryReport]:
        order_rows = self.db_session.execute(
            select(
                PurchaseOrderRecord.id,
                PurchaseOrderRecord.status,
                PurchaseOrderRecord.total,
            )
        ).all()
        line_rows = self.db_session.execute(
            select(
                PurchaseOrderLineRecord.purchase_order_id,
                PurchaseOrderLineRecord.quantity,
                PurchaseOrderLineRecord.received_quantity,
            )
        ).all()

        quantities: dict[int, tuple[int, int]] = {}
        for order_id, quantity, received_quantity in line_rows:
            ordered, received = quantities.get(order_id, (0, 0))
            quantities[order_id] = (ordered + quantity, received + received_quantity)

        summary: dict[str, ProcurementSummaryReport] = {}
        for order_id, status, total in order_rows:
            ordered, received = quantities.get(order_id, (0, 0))
            current = summary.get(status)
            summary[status] = ProcurementSummaryReport(
                status=status,
                order_count=(current.order_count if current else 0) + 1,
                total_value=(current.total_value if current else Decimal("0.00"))
                + Decimal(total or 0),
                ordered_quantity=(current.ordered_quantity if current else 0) + ordered,
                received_quantity=(current.received_quantity if current else 0) + received,
            )
        return [summary[status] for status in sorted(summary)]

    def stock_movement_summary(self) -> list[StockMovementSummaryReport]:
        rows = self.db_session.execute(
            select(
                InventoryMovementRecord.movement_type,
                func.count(InventoryMovementRecord.id),
                func.sum(InventoryMovementRecord.quantity),
            )
            .group_by(InventoryMovementRecord.movement_type)
            .order_by(InventoryMovementRecord.movement_type)
        ).all()
        return [
            StockMovementSummaryReport(
                movement_type=row[0],
                movement_count=int(row[1] or 0),
                total_quantity=int(row[2] or 0),
            )
            for row in rows
        ]
