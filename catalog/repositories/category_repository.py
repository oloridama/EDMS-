# this script handles the business operation of persisting categories that products fall into
from catalog.models.product import Product
from catalog.models.category import Category
from catalog.repositories.product_repository import ProductRepository
from shared.logging import log

class CategoryRepository:
    def __init__(self, category, product_repo):
        self.category = category if category else Category()
        self.product_repo = product_repo if product_repo else ProductRepository()
        self.categories = [self.category]
        
        pass

    def create_category(self, name, desc):
        """
        Method for creating a new category
        It takes a name and desc arguments to call the category model in order to create the category
        """
        self.category(name=name, description=desc)
        log("Category {name} created!")

    def category_exists(self, category_name: str) -> bool:
        # Check the category names list
        category = self.find_category(self.categories, category_name)
        if category == None:
            log("Category {name} not found, create category-call create_category()")
            return False
        log("Category {name} exists!")
        return True

    def add_product_to_category(self, product: Product, category_name):
        """
        Add product model to category
        """
        # Add product to category 
        product.category(name=category_name)

    def find_category(categories: list, category_name):
        for category in categories:
            if category == category_name:
                return category
        
    def check_product_category(self, product_name):
        for product in self.product_repo.catalog:
            if product.name == product_name:
                category = product.category
                return category


