from catalog.repositories.product_repository import ProductRepository
from catalog.repositories.category_repository import CategoryRepository
from catalog.models.product import Product

from shared.logging import log

class ProductService:
    def __init__(self, product_repo: ProductRepository, category_repo: CategoryRepository):
        """
        Service layer for product operations
        """
        self.product_repo = product_repo 
        self.category_repo = category_repo

    def add_to_catalog(
            self, 
            product_id,
            name,
            desc,
            brand,
            category_name,
            manufacturers,
            price
        ):
        """
        Adds a product to the business catalogs
        for new products about to be offered by the business
        """
        is_valid, category = self.category_repo.category_exists(category_name)
        if not is_valid:
            log(f"A product can only be added to an existing category!")
        else:
            try:
                new_product = Product(
                    product_id=product_id, 
                    name=name, 
                    description=desc,
                    brand=brand, 
                    category=category, 
                    manufacturers=manufacturers, 
                    price=price
                )
                log(f"New product {name} with {product_id} created by initialization successfully!")
                self.product_repo.add_product(new_product)
                log(f"Product added!")
            except Exception as e:
                log(f"The product was not added! Check your arguments: {e}")
                log(sentence=Exception, is_error=True)

    def remove_product_from_catalog(self, product_name):
        """
        Removes a product from the business catalog
        """
        try:
            self.product_repo.remove_product(product_name)
            log(f"Product-{product_name} successfully removed!")
        except Exception as e:
            log(f"Product removal failed: {e}")