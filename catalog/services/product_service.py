from catalog.repositories.product_repository import ProductRepository
from catalog.repositories.category_repository import CategoryRepository

from catalog.services.product_configuration_service import ProductConfigurationService
from catalog.services.specification_service import SpecificationService
from catalog.models.product import Product

from shared.logging import log

class ProductService:
    def __init__(
            self, 
            product_repo: ProductRepository, 
            category_repo: CategoryRepository, 
            config_service: ProductConfigurationService,
            spec_service: SpecificationService
        ):
        """
        Service layer for product operations
        :param product_repo: An instance of ProductRepository
        :param category_repo: An instance of CategoryRepository
        :param config_repo: An instance of ConfigurationRepository
        """
        self.product_repo = product_repo 
        self.category_repo = category_repo
        self.config_service = config_service
        self.spec_service = spec_service

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
            return

        try:
            # Build the complete object graph before saving anything. This prevents
            # an invalid configuration from leaving a partial product in the catalog.
            new_product = Product(
                product_id=product_id,
                name=name,
                description=desc,
                brand=brand,
                category=category,
                configurations=[]
            )

            configuration_fields = kwargs.get('configuration_fields', {})
            specification_args = kwargs.get('specifications')
            if not specification_args:
                raise ValueError("Product configuration requires specifications.")

            configuration = self.config_service.create_product_config(
                product=new_product,
                specs=[],
                price=price,
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

            for spec_name, spec_args in specification_args.items():
                specification = self.spec_service.create_specification(
                    spec_type_name=spec_args['spec_type_name'],
                    spec_type_value_type=spec_args['spec_type_value_type'],
                    allowed_values=spec_args.get('allowed_values', []),
                    value=spec_args.get('spec_value'),
                    category=category
                )
                configuration.specifications.append(specification)

            validation_errors = configuration.validate_specifications()
            if validation_errors:
                raise ValueError(
                    "Product configuration is invalid: "
                    + " ".join(validation_errors)
                )

            new_product.add_product_configuration(configuration)

            # Persistence happens only after all category and configuration checks pass.
            self.product_repo.add_product(new_product)
            self.config_service.config_repo.save_configuration(configuration)
            log(f"Product {new_product.name} added to the catalog!")

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