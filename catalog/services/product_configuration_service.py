from catalog.models.product_configuration import ProductConfiguration
from catalog.repositories.configuration_repository import ConfigurationRepository
from shared.logging import log

class ProductConfigurationService:
    def __init__(self, config_repo: ConfigurationRepository):
        self.config_repo = config_repo

    def create_product_config(self, product, specs, price, **others) -> ProductConfiguration:
        configuration = ProductConfiguration(
            product=product,
            specifications=specs,
            pricing=price,
            material=others.get('material'),
            weight=others.get('weight'),
            color=others.get('color'),
            size=others.get('size'),
            volume=others.get('volume'),
            length=others.get('length'),
            width=others.get('width'),
            unit=others.get('unit'),
            additional_features=others.get('additional_features')
        )

        return configuration

    