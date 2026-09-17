from dataclasses import dataclass

from catalog.models.specification import Specification

@dataclass
class Category:
    """
    class of category a product may fall into
    """
    name: str    # name of the category
    specifications: list[Specification]     # specifications that products in this category must adhere to
    description: str | None = None

    def add_specification(self, specification: Specification) -> None:
        """Add a specification to this category once."""
        if specification not in self.specifications:
            self.specifications.append(specification)