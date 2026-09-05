from dataclasses import dataclass

@dataclass
class Brand:
    """
    Brand class to represent a product brand.
    """
    name: str   # name of the brand
    products: list[str]  # List of product IDs associated with the brand