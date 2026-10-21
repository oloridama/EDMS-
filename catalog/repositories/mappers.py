from catalog.models.brand import Brand
from catalog.models.category import Category
from catalog.models.product import Product
from catalog.models.product_configuration import ProductConfiguration
from catalog.models.specification import (
    Specification,
    SpecificationType,
    SpecificationValueType,
)
from catalog.repositories.records import (
    CategoryRecord,
    ProductConfigurationRecord,
    ProductRecord,
)
from shared.pricing import Pricing, PricingRule


def category_from_record(record: CategoryRecord) -> Category:
    return Category(
        name=record.name,
        description=record.description,
        specification_types=[
            SpecificationType(
                name=specification_type.name,
                value_type=SpecificationValueType(specification_type.value_type),
                allowed_values=specification_type.allowed_values or [],
            )
            for specification_type in record.specification_types
        ],
    )


def configuration_from_record(
    record: ProductConfigurationRecord,
    product: Product,
) -> ProductConfiguration:
    return ProductConfiguration(
        product=product,
        specifications=[
            Specification(
                type=SpecificationType(
                    name=item.specification_type.name,
                    value_type=SpecificationValueType(item.specification_type.value_type),
                    allowed_values=item.specification_type.allowed_values or [],
                ),
                value=item.value,
            )
            for item in record.specifications
        ],
        pricing=Pricing(
            pricing_rules=[
                PricingRule(
                    min_quantity=rule.min_quantity,
                    max_quantity=rule.max_quantity,
                    unit_price=rule.unit_price,
                )
                for rule in record.pricing_rules
            ]
        ),
        material=record.material,
        weight=record.weight,
        color=record.color,
        size=record.size,
        volume=record.volume,
        length=record.length,
        width=record.width,
        unit=record.unit,
        additional_features=record.additional_features,
    )


def product_from_record(record: ProductRecord) -> Product:
    product = Product(
        product_id=record.product_id,
        name=record.name,
        description=record.description,
        brand=Brand(name=record.brand_name, products=[record.product_id]),
        category=category_from_record(record.category),
        configurations=[],
    )
    product.configurations.extend(
        configuration_from_record(configuration, product)
        for configuration in record.configurations
    )
    return product
