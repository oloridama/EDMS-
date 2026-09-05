from catalog.repositories.product_repository import ProductRepository
from catalog.models.product import Product
from catalog.models.category import Category
from catalog.models.pricing import Pricing, PricingRule
from shared.logging import log

class ProductService:
    def __init__(self, product_repo):
        self.product_repo = product_repo if product_repo else ProductRepository()
        pass

    def add_to_catalog(self, product):
        """
        Adds a product to the business catalogs
        for new products about to be offered by the business
        """
        try:
            self.product_repo.add_product(product)
            log("Product added!")
        except:
            log("The product was not added! Check your arguments")
            log(sentence=Exception, is_error=True)


    def create_product(
            self, 
            product: Product, 
        ):
        # create product by creating and instance of the Product model

        # initialize the product
        self.instantiate_product(
            product.product_id, 
            product.name, 
            product.description, 
            product.brand, 
            product.category, 
            product.manufacturers,
            product.pricing
        )

    def remove_product_from_catalog(self, product_name):
        try:
            self.product_repo.remove_product(product_name)
            log("Product-{product_name} successfully removed!")
        except:
            log("Product removal failed!")
        pass

    def instantiate_product(
            self, 
            id, 
            name, 
            desc, 
            brand, 
            category, 
            manufacturers: list, 
            category_name = None, 
            category_desc = None
    ):
        """
        Creates new product identities the business is ready to offer to customers
        """
        manufacturers = manufacturers[0] if len(manufacturers) == 1 else manufacturers
        category = category if category else Category(category_name, category_desc)
        try:
            self.product(id, name, desc, brand, category, manufacturers)
            log("New product {name} with {id} created successfully!")
        except:
            log("Failed to create the product: {Exception}")