class OrderLineRepository:
    def __init__(self, orderlines = None):
        self.orderlines = orderlines if orderlines else []

    def create_order_line_list(self, orderline):
        self.orderlines.append(orderline)