from procurement.models.purchase_line import PurchaseLine
from procurement.repositories.purchase_order_repository import PurchaseOrderRepository


class PurchaseLineService:
    def __init__(self, purchase_order_repository: PurchaseOrderRepository):
        self.purchase_order_repository = purchase_order_repository

    def create_purchase_line(self, purchase_line_data: dict) -> PurchaseLine:
        """
        Create a purchase line from a dictionary payload.
        The payload is expected to contain a product configuration, quantity,
        manufacturer, and unit price.
        """
        purchase_line = PurchaseLine(
            product=purchase_line_data.get("product_configuration"),
            quantity=purchase_line_data.get("quantity"),
            manufacturer=purchase_line_data.get("manufacturer"),
            unit_price=purchase_line_data.get("unit_price"),
        )
        return purchase_line

    def get_purchase_line(self, purchase_order_id, product_id):
        """Delegate persisted purchase-line retrieval to the owning order repository."""
        return self.purchase_order_repository.get_purchase_line(
            purchase_order_id,
            product_id,
        )