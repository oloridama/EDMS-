from catalog.models.order import Order

class OrderRepository:
    def __init__(self, orders: list[Order] = None):
        """
        Repository layer for order operations
        """
        self.orders = orders if orders else []

    def add_order(self, order: Order):
        """
        Adds an order to the repository"""
        self.orders.append(order)
