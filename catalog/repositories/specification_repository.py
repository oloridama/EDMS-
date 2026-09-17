from catalog.models.specification import Specification
from catalog.models.category import Category

class SpecificationRepository:
    def __init__(self):
        self.specifications = []
        self.category_specifications = {}

    def save_specification(self, specification: Specification, category: Category):
        category.add_specification(specification)
        if specification not in self.specifications:
            self.specifications.append(specification)
        self.category_specifications.setdefault(category.name, [])
        if specification not in self.category_specifications[category.name]:
            self.category_specifications[category.name].append(specification)

    def get_specifications(self) -> list[Specification]:
        return self.specifications

    def get_specification_by_name(self, name: str) -> Specification | None:
        for spec in self.specifications:
            if spec.name == name:
                return spec
        return None

    def get_specifications_by_category(self, category: Category) -> list[Specification]:
        return self.category_specifications.get(category.name, [])