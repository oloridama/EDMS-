from __future__ import annotations

from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from catalog.models.product import Product

from catalog.models.specification import Specification
from shared.pricing import Pricing

@dataclass
class ProductConfiguration:
    """
    ProductConfiguration class to represent the configuration details of a product.
    """
    product: Product  # Reference to the Product class
    specifications: list[Specification]   # Reference to the specifications that define this product configuration
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

    def validate_specifications(self) -> list[str]:
        """Return all validation errors for this configuration."""
        errors = []
        required_types = self.product.category.specification_types
        required_names = {specification_type.name for specification_type in required_types}
        actual_names = {specification.type.name for specification in self.specifications}

        for missing_name in sorted(required_names - actual_names):
            errors.append(f"Missing required specification: '{missing_name}'.")

        for extra_name in sorted(actual_names - required_names):
            errors.append(f"Specification '{extra_name}' is not allowed for this category.")

        for required_type in required_types:
            matching_specifications = [
                specification
                for specification in self.specifications
                if specification.type.name == required_type.name
            ]

            if len(matching_specifications) > 1:
                errors.append(
                    f"Specification '{required_type.name}' appears more than once."
                )
                continue

            if not matching_specifications:
                continue

            matching_specification = matching_specifications[0]
            if not required_type.validate_value(matching_specification.value):
                errors.append(
                    f"Invalid value for '{required_type.name}': "
                    f"{matching_specification.value!r}."
                )

        return errors

    def validate_spec(self) -> bool:
        """Return whether all required category specifications are valid."""
        return not self.validate_specifications()
            