from dataclasses import dataclass

@dataclass
class Category:
    """
    class of category a product may fall into
    """
    name: str    # name of the category
    description: str | None = None