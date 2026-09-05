from dataclasses import dataclass

from catalog.models.category import Category
from catalog.models.brand import Brand
from catalog.models.manufacturer import Manufacturer
from catalog.models.pricing import Pricing

@dataclass
class Product:
    """
    The model of the business product
    """
    product_id: str    # Unique identifier for the product
    name: str
    description: str
    brand: Brand      
    category: Category    # A reference of the hint type of the category the product falls into
    manufacturers: list[Manufacturer]       # a product can have multiple manufacturers
    unit_price: Pricing