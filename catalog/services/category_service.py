from catalog.models.category import Category
from catalog.models.specification import Specification, SpecificationType, SpecificationValueType
from catalog.repositories.category_repository import CategoryRepository
from catalog.services.specification_service import SpecificationService
from shared.logging import log
from shared.error_handling import CategoryAlreadyExistsError

class CategoryService:
    def __init__(self, category_repo: CategoryRepository, spec_service: SpecificationService):
        self.category_repo = category_repo
        self.spec_service = spec_service

    def create_category(
            self, 
            category_name: str, 
            specifications: list[Specification], 
            category_desc: str | None = None
        ):
        """
        Creates a new category using the CategoryRepository.
            :param category_name: The name of the category to create
            :param specifications: The specifications associated with the category
            :param category_desc: Optional description of the category
            :raises ValueError: If the category name is empty or whitespace
            :raises CategoryAlreadyExistsError: If the category already exists
        """
        if not category_name:
            raise ValueError("Category name cannot be empty.")
        if category_name != category_name.strip():
            raise ValueError("Category name cannot be empty or whitespace.")
        existing, _ = self.category_repo.category_exists(category_name)

        if existing is False:
            raise CategoryAlreadyExistsError(f"Category '{category_name}' already exists.")

        for spec in specifications:
            if self.spec_service.validate_specification(spec) is False:
                raise ValueError("Invalid specification provided.")
        
        category = Category(
            name=category_name, 
            specifications=specifications, 
            description=category_desc
        )
        self.category_repo.save_category(category)
        
    def get_product_category(self, product_name):
        """
        Retrieves the category of a product.
        """
        return self.category_repo.check_product_category(product_name)