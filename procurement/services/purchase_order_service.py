from procurement.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from procurement.models.purchase_line import PurchaseLine
from procurement.repositories.purchase_order_repository import PurchaseOrderRepository
from procurement.services.purchase_line_service import PurchaseLineService


class PurchaseOrderService:
    def __init__(
        self,
        purchase_line_service: PurchaseLineService,
        purchase_order_repository: PurchaseOrderRepository,
    ):
        self.purchase_line_service = purchase_line_service
        self.purchase_order_repository = purchase_order_repository

    def create_purchase_order(self, order_data: dict):
        """Create a draft order from line objects or purchase-line data dictionaries.

        Accepts either ``purchase_line`` for one line or ``purchase_lines`` for
        multiple lines. Each supplied line may already be a PurchaseLine or be
        a dictionary understood by PurchaseLineService.
        """
        supplier = order_data.get("supplier")
        if supplier is None:
            raise ValueError("A supplier is required to create a purchase order.")

        if "purchase_lines" in order_data:
            supplied_lines = order_data["purchase_lines"]
            if not isinstance(supplied_lines, list):
                raise TypeError("'purchase_lines' must be a list.")
        elif "purchase_line" in order_data:
            supplied_lines = [order_data["purchase_line"]]
        else:
            raise ValueError("Provide 'purchase_line' or 'purchase_lines'.")

        if not supplied_lines:
            raise ValueError("A purchase order must contain at least one line.")

        purchase_lines = []
        for line_data in supplied_lines:
            if isinstance(line_data, PurchaseLine):
                purchase_lines.append(line_data)
            elif isinstance(line_data, dict):
                purchase_lines.append(
                    self.purchase_line_service.create_purchase_line(line_data)
                )
            else:
                raise TypeError(
                    "Each purchase line must be a PurchaseLine or a line-data dictionary."
                )

        purchase_order = PurchaseOrder(
            supplier=supplier,
            purchase_lines=purchase_lines,
        )
        self.purchase_order_repository.save_purchase_order(purchase_order)
        return purchase_order

    def get_purchase_order(self, order_id):
        return self.purchase_order_repository.get_purchase_order(order_id)

    def update_purchase_order(self, order_id, update_data):
        if not isinstance(update_data, dict) or not update_data:
            raise ValueError("Purchase order updates must be a non-empty dictionary.")
        unsupported_fields = set(update_data) - {"status"}
        if unsupported_fields:
            fields = ", ".join(sorted(unsupported_fields))
            raise ValueError(f"Unsupported purchase order update field(s): {fields}.")

        requested_status = update_data["status"]
        try:
            next_status = PurchaseOrderStatus(requested_status)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Unknown purchase order status: {requested_status!r}.") from error

        order = self.purchase_order_repository.get_purchase_order(order_id)
        if order is None:
            raise ValueError(f"Purchase order {order_id} was not found.")

        current_status = PurchaseOrderStatus(order.status)
        allowed_transitions = {
            PurchaseOrderStatus.DRAFT: {PurchaseOrderStatus.APPROVED},
            PurchaseOrderStatus.APPROVED: {PurchaseOrderStatus.SENT},
            PurchaseOrderStatus.SENT: {PurchaseOrderStatus.PARTIALLY_RECEIVED},
            PurchaseOrderStatus.PARTIALLY_RECEIVED: {PurchaseOrderStatus.COMPLETED},
            PurchaseOrderStatus.COMPLETED: set(),
        }
        if next_status not in allowed_transitions[current_status]:
            raise ValueError(
                f"Invalid purchase order status transition from "
                f"'{current_status.value}' to '{next_status.value}'."
            )

        total_ordered = sum(line.quantity for line in order.lines)
        total_received = sum(line.received_quantity for line in order.lines)
        if next_status is PurchaseOrderStatus.APPROVED and not order.lines:
            raise ValueError("A purchase order must contain at least one line before approval.")
        if next_status is PurchaseOrderStatus.PARTIALLY_RECEIVED and not (
            0 < total_received < total_ordered
        ):
            raise ValueError(
                "A purchase order can be marked partially received only when some, "
                "but not all, quantities have been received."
            )
        if next_status is PurchaseOrderStatus.COMPLETED and total_received == 0:
            raise ValueError("A partially received order must have received some goods.")

        order.status = next_status.value
        self.purchase_order_repository.db_session.flush()
        return order

    def delete_purchase_order(self, order_id):
        self.purchase_order_repository.delete_purchase_order(order_id)