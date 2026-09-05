from dataclasses import dataclass

from catalog.models.product import Product

@dataclass
class ProductConfiguration:
    """
    ProductConfiguration class to represent the configuration details of a product.
    """
    product: Product  # Reference to the Product class
    material: str
    weight: float
    color: str | None
    size: str | None
    volume: float | None
    length: float | None
    width: float | None
    unit: str | None
    additional_features: str | None