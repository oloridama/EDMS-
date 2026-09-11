# this script handles the business operation of persisting categories that products fall into
from catalog.models.product import Product
from catalog.models.category import Category
from catalog.repositories.product_repository import ProductRepository
from shared.logging import log

class CategoryRepository:
    def __init__(self, category: Category, product_repo: ProductRepository):
        """
        Repository layer for category operations
        """
        self.category = category 
        self.product_repo = product_repo
        self.categories = [self.category]

    def create_category(self, name, desc):
        """
        Method for creating a new category
        It takes a name and desc arguments to call \
            the category model in order to create the category
        """
        self.category(name=name, description=desc)
        log(f"Category {name} created!")

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

    def add_product_to_category(self, product: Product, category_name):
        """
        Add product model to category
        """
        # Add product to category by 
        # 1. initialize the instance of category
        category = Category(name=category_name)
        # 2. assign to the existing product category object to create the relationship
        product.category = category

    def find_category(categories: list, category_name: str) -> Category | None:
        """
        Finds a category by name in the list of categories
        """
        for category in categories:
            if category.name == category_name:
                return category
        return None

    def check_product_category(self, product_name: str):
        """
        Checks the category of a product by name
        """
        for product in self.product_repo.catalog:
            if product.name == product_name:
                category = product.category
                return category


