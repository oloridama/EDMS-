class CategoryAlreadyExistsError(Exception):
    """Raised when attempting to persist a category name that is already in use."""

    def __init__(self, category_name: str) -> None:
        self.category_name = category_name
        super().__init__(f"Category '{category_name}' already exists.")


class SpecificationAlreadyExistsError(Exception):
    """Raised when a category already has the same specification type and value."""

    def __init__(self, category_name: str, specification_type: str, value: object) -> None:
        self.category_name = category_name
        self.specification_type = specification_type
        self.value = value
        super().__init__(
            f"Specification '{specification_type}' with value {value!r} "
            f"already exists for category '{category_name}'."
        )