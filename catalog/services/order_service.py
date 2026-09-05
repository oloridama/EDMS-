# The script is the entry point to creating an Order
# This service will serve both the OrderLine repo and order repo as well
# The number of orderlines in an order cannot be known initially before the order is created
# Hence the order service can not be built around an orderline being constructed in the constructor 
from catalog.models.product_configuration import ProductConfiguration
from catalog.models.order import Order
from catalog.models.orderline import OrderLine
from catalog.repositories.orderline_repository import OrderLineRepository
from catalog.repositories.pricing_repository import PricingRepository as pricing_repo

class OrderService:
    def __init__(self, order_repo, orderline_repo):
        """
        The order class constructor creates an order object with the parameters
        :param order_repo: repository for persisting and retrieving orders
        :param orderline_repo: repository for persisting and retrieving orderlines
        """
        self.order_repo = order_repo
        self.orderline_repo = orderline_repo if orderline_repo else OrderLineRepository()
        pass

    def create_order(
            self, 
            order_info: list[dict],
            order_requester
        ):
        """
        :param order_info: list of dict of info to be provided by the user 
            creating an order, contain multiple products being requested. 
            So each dict is a data structure that contains the required info
            for creating an instance of the Product it represents

        :param order_requester: the name of whoever is making the requests
        it may be a customer or a branch
        """
        # Accessing the information will require us to
        # destructure kwargs for the Product fields

        i = 0
        while i < len(order_info):

            # 1. Get the dict (defaults to an empty dict if missing)
            product_fields = order_info[i]
            
            if product_fields:
                # 2. Extract and remove order-specific fields from the dict
                # Using .pop(key, default_value) ensures it won't crash if missing
                quantity = product_fields.pop("quantity", 1)

                # This is a correct placeholder for now
                # Correct implementaion would be to access it from Pricing.pricing_rule
                # As the unit_price should have been set at product creation
                unit_price = product_fields.pop("unit_price", 0.0)  # placeholder

                # 3. Now product_fields only contains actual product parameters!
                new_product = ProductConfiguration(**product_fields)
                order_line = OrderLine(new_product, quantity, unit_price)

                # 4. Persist the orderline
                #self.orderline_repo.save_orderline(order_line)
                self.orderline_repo.create_order_line_list(order_line)

        # 5. persist the order
        order_lines = self.orderline_repo.orderlines
        order = self.save_order(order_requester, order_lines)
        print(f"--- Order details for {order_requester} ---")
        self.order_repo.add_order(order)

        # 6. print out the order to stdout
        for line in order.orderlines:
            # i. Access the ProductConfiguration from the line
            config = line.product_configuration

            # ii. Access the custom Product dataclass inside that configuration
            product_dataclass = config.product

            # iii. Grab the name string from the dataclass
            product_name = product_dataclass.name     # compact one-liner - line.product_configuration.product.name
            print(f"{product_name} | {line.quantity} | ${line.unit_price}  \
                  ->  {pricing_repo.total(line.unit_price * line.quantity)}")

        # 6. clear the orderlines after saving 
        # for potential new operations
        order_lines.clear()

    def save_order(requester: str, orderlines: list) -> Order:
        # Create Order object by initializing Order
        order = Order(requester, orderlines)
        return order

    