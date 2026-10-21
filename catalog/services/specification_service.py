from catalog.models.specification import Specification, SpecificationType, SpecificationValueType
from catalog.repositories.specification_repository import SpecificationRepository
from shared.logging import log


class SpecificationService:
    def __init__(self, specification_repo: SpecificationRepository | None = None):
        """Initializes the SpecificationService with the provided SpecificationRepository.
        """
        self.specification_repo = specification_repo

    def create_spec_type(
            self, 
            name: str, 
            value_type: SpecificationValueType, 
            allowed_values: list[str | int | float | bool] = None
        ) -> SpecificationType:
        """
        Creates a new specification type.
            :param name: The name of the specification type
            :param value_type: The value type of the specification (e.g., text, enum, number, boolean)
            :param allowed_values: Optional list of allowed values for the specification type
            :raises ValueError: If the specification type is invalid
        """
        if not name:
            raise ValueError("Specification type name cannot be empty.")
        if not value_type:
            raise ValueError("Specification value type cannot be None.")
        if allowed_values is None:
            allowed_values = []
        spec_type = SpecificationType(name=name, value_type=value_type, allowed_values=allowed_values)
        return spec_type
    
    def create_specification(
            self,
            spec_type_name,
            spec_type_value_type,
            allowed_values,
            value,
            category,
        ) -> Specification:
        """
        Creates and validates a specification for a specific category.
            :param spec_type_name: The name of the specification type
            :param spec_type_value_type: The value type of the specification
            :param allowed_values: Optional list of allowed values for the specification type
            :param value: The value of the specification
            :param category: The category this specification belongs to
            :raises ValueError: If the specification is invalid
        """
        if category is None:
            raise ValueError("Category cannot be None when creating a specification.")

        spec_type = self.create_spec_type(spec_type_name, spec_type_value_type, allowed_values)
        specification = Specification(type=spec_type, value=value)
        if not self.validate_specification(specification):
            raise ValueError("Invalid specification provided.")

        return specification

    def validate_specification(self, specification: Specification) -> bool:
        """
        Validates the provided specification.
            :param specification: The specification to validate
            :return: True if valid, False otherwise
        """
        if not specification:
            log.error("Specification is None.")
            return False
        if not specification.type:
            log.error("Specification type is None.")
            return False
        if not specification.type.validate_value(specification.value):
            log.error(f"Specification value '{specification.value}' is invalid for type '{specification.type.name}'.")
            return False
        return True