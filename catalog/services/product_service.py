from itertools import product

from catalog.models.product_configuration import ProductConfiguration
from catalog.repositories.configuration_repository import ConfigurationRepository
from catalog.repositories.product_repository import ProductRepository
from catalog.repositories.category_repository import CategoryRepository
from catalog.models.product import Product

from shared.logging import log

class ProductService:
    def __init__(
            self, 
            product_repo: ProductRepository, 
            category_repo: CategoryRepository, 
            config_repo: ConfigurationRepository
        ):
        """
        Service layer for product operations
        :param product_repo: An instance of ProductRepository
        :param category_repo: An instance of CategoryRepository
        :param config_repo: An instance of ConfigurationRepository
        """
        self.product_repo = product_repo 
        self.category_repo = category_repo
        self.config_repo = config_repo

    def add_to_catalog(
            self, 
            product_id,
            name,
            desc,
            brand,
            category_name,
            price,
            **kwargs
        ):
        """
        Adds a product to the business catalogs
        for new products about to be offered by the business
        :param product_id: Unique identifier for the product
        :param name: Name of the product
        :param desc: Description of the product
        :param brand: Brand of the product
        :param category_name: Name of the category the product belongs to
        :param price: Price of the product configuration
        :param kwargs: Additional configuration fields for the product
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
                    category=category
                )
                log(f"New product {name} with {product_id} created by initialization successfully!")
                self.product_repo.add_product(new_product)
                log(f"Product added!")

                configuration_fields = kwargs.get('configuration_fields', {})
                configuration = ProductConfiguration(
                    product=new_product,
                    pricing=price,
                    material=configuration_fields.get('material'),
                    weight=configuration_fields.get('weight'),
                    color=configuration_fields.get('color'),
                    size=configuration_fields.get('size'),
                    volume=configuration_fields.get('volume'),
                    length=configuration_fields.get('length'),
                    width=configuration_fields.get('width'),
                    unit=configuration_fields.get('unit'),
                    additional_features=configuration_fields.get('additional_features')
                )
                new_product.add_product_configuration(configuration)
                log(f"Product configuration added to {new_product.name}!")

                self.config_repo.save_configuration(configuration)
                log(f"Product configuration saved to the repository!")

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