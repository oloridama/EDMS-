class OrderLineRepository:
    def __init__(self, orderlines = None):
        """
        Initializes the OrderLineRepository with a list of order lines.
        """
        self.orderlines = orderlines if orderlines else []

    def create_order_line_list(self, orderline):
        self.orderlines.append(orderline)