from catalog.models.product import Product
from shared.logging import log

class ProductRepository:
    """
    class object with methods for performing the business operations
    """
    def __init__(self, catalog: list[Product]):
        self.catalog = catalog if catalog else []
        pass

    def add_product(self, product: Product):
        """
        The method handles the business operation of persisting the product intended to be added when called
        """
        self.catalog.append(product)

    def remove_product(self, products_catalog: list, product_name):
        """
        The method handles the deletion of product from the business catalog
        :param products_catalog: This is the catalog to be deleted from
        :param product: This is the product object to be deleted from the catalog
        """
        for product in products_catalog:
            if product.name == product_name:
                products_catalog.remove(product)