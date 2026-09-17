from catalog.models.specification import Specification
from catalog.repositories.specification_repository import SpecificationRepository
from shared.logging import log
from shared.error_handling import SpecificationAlreadyExistsError

class SpecificationService:
    def __init__(self, specification_repo: SpecificationRepository):
        self.specification_repo = specification_repo

    def create_specification(self, specification: Specification):
        """
        Creates a new specification using the SpecificationRepository.
            :param specification: The specification to create
            :raises ValueError: If the specification is invalid
            :raises SpecificationAlreadyExistsError: If the specification already exists
        """
        if not self.validate_specification(specification):
            raise ValueError("Invalid specification provided.")

        existing = self.specification_repo.get_specification_by_name(specification.name)
        if existing is not None:
            raise SpecificationAlreadyExistsError(f"Specification '{specification.name}' already exists.")

        self.specification_repo.save_specification(specification)

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