# The orderline is a single line of product ordered within a list of "Order

from dataclasses import dataclass
from decimal import Decimal

from catalog.models.product_configuration import ProductConfiguration

@dataclass
class OrderLine:
    """
    The model of an orderline, it contain details of a request
    """
    product_configuration: ProductConfiguration
    quantity: int
    unit_price: Decimal   # Using Decimal instead of float because money needs exact decimal arithmetic

