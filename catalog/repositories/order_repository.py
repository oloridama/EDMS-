from catalog.models.order import Order

class OrderRepository:
    def __init__(self, orders):
        self.orders = orders if orders else []
        pass

    def add_order(self, order: Order):
        self.orders.append(order)
