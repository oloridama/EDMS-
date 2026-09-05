from dataclasses import dataclass

from catalog.models.orderline import OrderLine

@dataclass
class Order:
    """
    model representing an order, it holds info of the name of who is placing the order and the orderlines
    """
    requester: str
    order_lines: list[OrderLine]