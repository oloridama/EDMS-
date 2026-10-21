from dataclasses import dataclass

from catalog.models.specification import SpecificationType

@dataclass
class Category:
    """
    class of category a product may fall into
    """
    name: str    # name of the category
    specification_types: list[SpecificationType]     # specification types that products in this category must adhere to
    description: str | None = None

    def add_specification_type(self, specification_type: SpecificationType) -> None:
        """Add a required specification type to this category once."""
        # Check specification type name is unique within the category
        if any(spec.name == specification_type.name for spec in self.specification_types):
            raise ValueError("Specification type name must be unique within the category")

        self.specification_types.append(specification_type)