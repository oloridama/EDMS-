# this script handles the business operation of persisting categories that products fall into
from catalog.models.product import Product
from catalog.models.category import Category
from catalog.repositories.product_repository import ProductRepository
from shared.logging import log

class CategoryRepository:
    def __init__(self, categories: list[Category]):
        """
        Repository layer for category operations
        """
        self.categories = categories

    def save_category(self, category: Category):
        """
        Method for creating a new category
        It takes a name and desc arguments to call \
            the category model in order to create the category
        """
        self.categories.append(category)
        log(f"Category {category.name} created!")

    def category_exists(self, category_name: str) -> tuple[bool, Category | None]:
        """
        Checks if a category exists in the list of categories
        """
        # Check the category names list
        category = self.find_category(self.categories, category_name)
        if category == None:
            log(f"Category {category_name} not found! Create category first!")
            return False, None
        log(f"Category {category.name} exists!")
        return True, category

    def find_category(categories: list, category_name: str) -> Category | None:
        """
        Finds a category by name in the list of categories
        """
        for category in categories:
            if category.name == category_name:
                return category
        return None



