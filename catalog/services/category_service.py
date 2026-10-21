from catalog.models.category import Category
from catalog.repositories.category_repository import CategoryRepository
from catalog.services.specification_service import SpecificationService
from shared.error_handling import CategoryAlreadyExistsError

class CategoryService:
    def __init__(
            self, 
            category_repo: CategoryRepository, 
            spec_service: SpecificationService
        ):
        """Initializes the CategoryService with the provided CategoryRepository and SpecificationService.
            :param category_repo: An instance of CategoryRepository for category-related operations
            :param spec_service: An instance of SpecificationService for specification-related operations
        """
        self.category_repo = category_repo
        self.spec_service = spec_service

    def create_category(
            self,
            category_name: str,
            specifications_args: dict[str, dict],
            category_desc: str | None = None
        ):
        """
        Creates a new category using the CategoryRepository.
            :param category_name: The name of the category to create
            :param specifications_args: The arguments for creating specifications associated with the category
            :param category_desc: Optional description of the category
            :raises ValueError: If the category name is empty or whitespace
            :raises CategoryAlreadyExistsError: If the category already exists
        """
        if not category_name or category_name.strip() != category_name:
            raise ValueError("Category name cannot be empty or whitespace.")

        if not specifications_args:
            raise ValueError("Category must include at least one specification.")

        exists, _ = self.category_repo.category_exists(category_name)
        if exists:
            raise CategoryAlreadyExistsError(category_name)

        category = Category(
            name=category_name,
            specification_types=[],
            description=category_desc,
        )

        for spec_name, spec_details in specifications_args.items():
            specification_type = self.spec_service.create_spec_type(
                name=spec_details.get("spec_type_name", spec_name),
                value_type=spec_details["spec_type_value_type"],
                allowed_values=spec_details.get("allowed_values", []),
            )
            category.add_specification_type(specification_type)

        self.category_repo.save_category(category)
        
    def get_product_category(self, product_name):
        """
        Retrieves the category of a product.
        """
        return self.category_repo.check_product_category(product_name)