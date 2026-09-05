from catalog.repositories.category_repository import CategoryRepository
from shared.logging import log

class CategoryService:
    def __init__(self, category_repo):
        self.category_repo = category_repo if category_repo else CategoryRepository()
        pass

    def add_to_category(self, product, category_name, category_desc):
        try:
            # check if category exists
            if self.category_repo.category_exists(category_name):
                self.category_repo.add_product_to_category(product)
                log("Product added to category {category_name} successfully!")
            else:
                # Create category
                self.category_repo.create_category(category_name, category_desc)
                self.category_repo.add_product_to_category(product)
                log("Product added to category {category_name} successfully!")
        except:
            # Log error message if theres an error from the user inputing wrong parameters
            log("The operation failed due to: {NameError}", True)

    def get_product_category(self, product_name):
            self.category_repo.check_product_category(product_name)