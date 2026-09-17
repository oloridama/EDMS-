from dataclasses import dataclass

from catalog.models.product import Product
from shared.pricing import Pricing

@dataclass
class ProductConfiguration:
    """
    ProductConfiguration class to represent the configuration details of a product.
    """
    product: Product  # Reference to the Product class
    pricing: Pricing
    material: str | None
    weight: float | None
    color: str | None
    size: str | None
    volume: float | None
    length: float | None
    width: float | None
    unit: str | None
    additional_features: str | None