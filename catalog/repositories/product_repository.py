from decimal import Decimal

from catalog.models.product import Product
from shared.logging import log

class ProductRepository:
    """
    class object with methods for performing the business operations
    """
    def __init__(self, catalog: list[Product]):
        self.catalog = catalog if catalog else []

    def add_product(self, product: Product):
        """
        The method handles the business operation of persisting \
        the product intended to be added when called
        """
        self.catalog.append(product)

    def remove_product(
            self, 
            products_catalog: list, 
            product_name: str
        ) -> None:
        """
        The method handles the deletion of product from the business catalog
            :param products_catalog: This is the catalog to be deleted from
            :param product_name: This is the name of the product to be deleted from the catalog
        """
        for product in products_catalog:
            if product.name == product_name:
                products_catalog.remove(product)
                log.info(f"Product {product_name} removed from catalog")
                return
        log.warning(f"Product not found in catalog: {product_name}")

    def check_product_unit_price(
            self, 
            product_name: str
        ) -> Decimal | None:
        """
        The method handles the retrieval of the unit price \
            of a product in the catalog
            :param product_name: This is the name of the product \
                whose unit price is to be retrieved
            :return: The unit price of the product if found, else None
        """
        for product in self.catalog:
            if product_name == product.name:
                return product.unit_price 
        return None

    def add_new_manufacturer(
            self, 
            product_name: str, 
            manufacturer: str
        ) -> None:
        """
        The method handles the addition of a new manufacturer \
            to an existing product in the catalog
            :param product_name: This is the name of the product \
                to which the manufacturer is to be added
            :param manufacturer: This is the name of the \
                manufacturer to be added to the product
        """
        for product in self.catalog:
            if product_name == product.name:
                product.manufacturers.append(manufacturer)
                log.info(f"Manufacturer {manufacturer} added to product {product_name}")
                return
        log.warning(f"Product not found: {product_name}")