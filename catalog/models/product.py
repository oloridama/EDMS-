from dataclasses import dataclass

from catalog.models.category import Category
from catalog.models.brand import Brand
from catalog.models.product_configuration import ProductConfiguration

@dataclass
class Product:
    """
    The model of the business product
    """
    product_id: str    # Unique identifier for the product
    name: str
    description: str
    brand: Brand      
    category: Category    # A reference of the hint type of the category the product falls into     
    configurations: list[ProductConfiguration]  # a product can have multiple configurations

    def add_product_configuration(self, configuration: ProductConfiguration):
        """
        Adds a product configuration to the product's configurations list.
        :param configuration: An instance of ProductConfiguration to be added
        """
        # Ensure that the configuration's product matches this product
        if configuration.product is not self:
            raise ValueError("Configuration's product does not match this product.")
        self.configurations.append(configuration)