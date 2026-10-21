from decimal import Decimal

from catalog.models.product_configuration import ProductConfiguration
from inventory.repositories.inventory_repository import InventoryLotRepository
from sales.models.sales_order import (
    Customer,
    SalesOrder,
    SalesOrderLine,
    SalesOrderStatus,
)
from sales.repositories.sales_order_repository import SalesOrderRepository


class SalesOrderService:
    def __init__(
        self,
        sales_order_repository: SalesOrderRepository,
        inventory_repository: InventoryLotRepository,
        pricing_repository=None,
        product_repository=None,
    ):
        self.sales_order_repository = sales_order_repository
        self.inventory_repository = inventory_repository
        self.pricing_repository = pricing_repository
        self.product_repository = product_repository

    def create_order(
        self,
        customer: Customer,
        warehouse_id: str,
        lines: list[dict],
    ) -> SalesOrder:
        if not warehouse_id:
            raise ValueError("A warehouse is required for a sales order.")
        if not lines:
            raise ValueError("A sales order must contain at least one line.")

        order_lines = []
        for line_data in lines:
            configuration = line_data.get("product_configuration")
            configuration_id = line_data.get("configuration_id")
            quantity = line_data.get("quantity")
            if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
                raise ValueError("Order-line quantity must be a positive integer.")

            if not isinstance(configuration, ProductConfiguration):
                if configuration_id is None:
                    raise ValueError("Each sales line requires a configuration_id.")
                configuration = self.sales_order_repository.get_configuration(
                    configuration_id
                )
            if configuration is None:
                raise ValueError(
                    f"Product configuration {configuration_id} was not found."
                )
            if configuration_id is None:
                configuration_id = self.sales_order_repository.get_configuration_id(
                    configuration
                )
            unit_price = self._resolve_unit_price(
                configuration,
                quantity,
                line_data.get("unit_price"),
            )
            order_lines.append(
                SalesOrderLine(
                    product_configuration=configuration,
                    configuration_id=configuration_id,
                    quantity=quantity,
                    unit_price=unit_price,
                )
            )
        order = SalesOrder(customer, warehouse_id, order_lines)
        self.sales_order_repository.save_order(order)
        return order

    def _resolve_unit_price(
        self,
        configuration: ProductConfiguration,
        quantity: int,
        explicit_price,
    ) -> Decimal:
        """Resolve price from configuration tiers, then catalog fallbacks."""
        if explicit_price is not None:
            price = Decimal(str(explicit_price))
        else:
            matching_rules = [
                rule
                for rule in configuration.pricing.pricing_rules
                if (rule.min_quantity is None or quantity >= rule.min_quantity)
                and (rule.max_quantity is None or quantity <= rule.max_quantity)
            ]
            if len(matching_rules) > 1:
                raise ValueError(f"Multiple pricing tiers match quantity {quantity}.")
            if matching_rules:
                price = Decimal(str(matching_rules[0].unit_price))
            else:
                product_name = configuration.product.name
                price = None
                if self.pricing_repository is not None:
                    stored_price = self.pricing_repository.get_price(product_name)
                    if stored_price is not None:
                        price = Decimal(str(stored_price))
                if price is None and self.product_repository is not None:
                    stored_price = self.product_repository.check_product_unit_price(
                        product_name,
                        quantity,
                    )
                    if stored_price is not None:
                        price = Decimal(str(stored_price))
                if price is None:
                    raise ValueError(
                        f"No price is configured for product '{product_name}' "
                        f"at quantity {quantity}."
                    )

        if price < 0:
            raise ValueError("Order-line unit price cannot be negative.")
        return price

    def get_order(self, order_id: int) -> SalesOrder | None:
        return self.sales_order_repository.get_order(order_id)

    def confirm_payment(self, order_id: int) -> SalesOrder:
        order = self._get_required_order(order_id)
        for line in order.lines:
            if self.inventory_repository.get_available_stock(
                str(line.configuration_id),
                order.warehouse_id,
            ) < line.quantity:
                raise ValueError(
                    f"Insufficient stock for configuration {line.configuration_id}."
                )
        order.mark_paid()
        for line in order.lines:
            self.inventory_repository.reserve_stock(
                str(line.configuration_id),
                order.warehouse_id,
                line.quantity,
                str(order_id),
            )
        self.sales_order_repository.save_order(order)
        return order

    def start_picking(self, order_id: int) -> SalesOrder:
        order = self._get_required_order(order_id)
        order.start_picking()
        self.sales_order_repository.save_order(order)
        return order

    def record_fulfillment(
        self,
        order_id: int,
        configuration_id: int,
        quantity: int,
    ) -> SalesOrder:
        order = self._get_required_order(order_id)
        line = next(
            (
                item
                for item in order.lines
                if item.configuration_id == configuration_id
            ),
            None,
        )
        if line is None:
            raise ValueError(
                f"Configuration {configuration_id} is not on sales order {order_id}."
            )
        order.record_fulfillment(line, quantity)
        self.sales_order_repository.save_order(order)
        return order

    def mark_packed(self, order_id: int) -> SalesOrder:
        order = self._get_required_order(order_id)
        order.mark_packed()
        self.sales_order_repository.save_order(order)
        return order

    def dispatch(self, order_id: int) -> SalesOrder:
        order = self._get_required_order(order_id)
        movements = order.record_dispatch()
        for configuration_id, quantity in movements.items():
            self.inventory_repository.dispatch_reserved_stock(
                str(configuration_id),
                order.warehouse_id,
                quantity,
                str(order_id),
            )
        self.sales_order_repository.save_order(order)
        return order

    def mark_delivered(self, order_id: int) -> SalesOrder:
        order = self._get_required_order(order_id)
        order.deliver()
        self.sales_order_repository.save_order(order)
        return order

    def complete(self, order_id: int) -> SalesOrder:
        order = self._get_required_order(order_id)
        order.complete()
        self.sales_order_repository.save_order(order)
        return order

    def cancel(self, order_id: int) -> SalesOrder:
        order = self._get_required_order(order_id)
        if order.status not in {SalesOrderStatus.CREATED, SalesOrderStatus.PAID}:
            raise ValueError("Only created or paid orders can be cancelled.")
        if order.status is SalesOrderStatus.PAID:
            for line in order.lines:
                self.inventory_repository.release_reserved_stock(
                    str(line.configuration_id),
                    order.warehouse_id,
                    line.quantity,
                    str(order_id),
                )
        order.status = SalesOrderStatus.CANCELLED
        self.sales_order_repository.save_order(order)
        return order

    def _get_required_order(self, order_id: int) -> SalesOrder:
        order = self.sales_order_repository.get_order(order_id)
        if order is None:
            raise ValueError(f"Sales order {order_id} was not found.")
        return order
