# This script defines the Pricing class and its subclasses for different pricing tiers in a product catalog.
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class PricingRule:
    """
    PricingRule class to represent different pricing rules for a product.
    """
    min_quantity: int  | None # The quantity determines the product's pricing tier (e.g., retail, wholesale, bulk)
    max_quantity: int  | None # The quantity determines the product's pricing tier (e.g., retail, wholesale, bulk)
    unit_price: Decimal  # The price per unit for the specified quantity range

@dataclass
class Pricing:
    """
    Pricing class to represent the overall pricing structure for a product.
    """
    pricing_rules: list[PricingRule]  # List of PricingRule objects to define different pricing tiers for a product