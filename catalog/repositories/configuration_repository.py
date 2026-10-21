from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from catalog.models.product_configuration import ProductConfiguration
from catalog.repositories.mappers import configuration_from_record, product_from_record
from catalog.repositories.records import (
    CategoryRecord,
    ConfigurationSpecificationRecord,
    PricingRuleRecord,
    ProductConfigurationRecord,
    ProductRecord,
)


class ConfigurationRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def save_configuration(self, configuration: ProductConfiguration) -> int:
        product = self.db_session.scalar(
            select(ProductRecord)
            .options(selectinload(ProductRecord.category))
            .where(ProductRecord.product_id == configuration.product.product_id)
        )
        if product is None:
            raise ValueError(
                f"Product '{configuration.product.product_id}' must be saved before its configuration."
            )

        type_records = {
            item.name: item
            for item in self.db_session.scalars(
                select(CategoryRecord)
                .options(selectinload(CategoryRecord.specification_types))
                .where(CategoryRecord.id == product.category_id)
            ).one().specification_types
        }
        persisted_specifications = []
        for specification in configuration.specifications:
            specification_type = type_records.get(specification.type.name)
            if specification_type is None:
                raise ValueError(
                    f"Specification type '{specification.type.name}' is not required "
                    f"by product category '{product.category.name}'."
                )
            persisted_specifications.append(
                ConfigurationSpecificationRecord(
                    specification_type=specification_type,
                    value=specification.value,
                )
            )

        record = ProductConfigurationRecord(
            product=product,
            material=configuration.material,
            weight=configuration.weight,
            color=configuration.color,
            size=configuration.size,
            volume=configuration.volume,
            length=configuration.length,
            width=configuration.width,
            unit=configuration.unit,
            additional_features=configuration.additional_features,
            specifications=persisted_specifications,
            pricing_rules=[
                PricingRuleRecord(
                    min_quantity=rule.min_quantity,
                    max_quantity=rule.max_quantity,
                    unit_price=rule.unit_price,
                )
                for rule in configuration.pricing.pricing_rules
            ],
        )
        self.db_session.add(record)
        self.db_session.flush()
        return record.id

    def get_configurations(self, product_id: str) -> list[ProductConfiguration]:
        product = self.db_session.scalar(
            select(ProductRecord)
            .options(
                selectinload(ProductRecord.category).selectinload(
                    CategoryRecord.specification_types
                ),
                selectinload(ProductRecord.configurations).selectinload(
                    ProductConfigurationRecord.specifications
                ),
                selectinload(ProductRecord.configurations).selectinload(
                    ProductConfigurationRecord.pricing_rules
                ),
            )
            .where(ProductRecord.product_id == product_id)
        )
        if product is None:
            return []
        domain_product = product_from_record(product)
        return domain_product.configurations

    def get_configuration(self, configuration_id: int) -> ProductConfiguration | None:
        record = self.db_session.scalar(
            select(ProductConfigurationRecord)
            .options(
                selectinload(ProductConfigurationRecord.product)
                .selectinload(ProductRecord.category)
                .selectinload(CategoryRecord.specification_types),
                selectinload(ProductConfigurationRecord.specifications),
                selectinload(ProductConfigurationRecord.pricing_rules),
            )
            .where(ProductConfigurationRecord.id == configuration_id)
        )
        if record is None:
            return None
        return configuration_from_record(record, product_from_record(record.product))

    def get_configuration_id(self, configuration: ProductConfiguration) -> int:
        records = self.db_session.scalars(
            select(ProductConfigurationRecord)
            .options(
                selectinload(ProductConfigurationRecord.product),
                selectinload(ProductConfigurationRecord.specifications),
                selectinload(ProductConfigurationRecord.pricing_rules),
            )
            .join(ProductRecord)
            .where(ProductRecord.product_id == configuration.product.product_id)
        ).all()
        for record in records:
            candidate = self.get_configuration(record.id)
            if candidate is not None and self._same_configuration(candidate, configuration):
                return record.id
        raise ValueError(
            f"Product configuration for '{configuration.product.product_id}' was not found."
        )

    @staticmethod
    def _same_configuration(
        first: ProductConfiguration,
        second: ProductConfiguration,
    ) -> bool:
        scalar_fields = (
            "material", "weight", "color", "size", "volume", "length", "width",
            "unit", "additional_features",
        )
        if any(getattr(first, field) != getattr(second, field) for field in scalar_fields):
            return False
        first_specs = {(item.type.name, item.value) for item in first.specifications}
        second_specs = {(item.type.name, item.value) for item in second.specifications}
        first_prices = {
            (item.min_quantity, item.max_quantity, item.unit_price)
            for item in first.pricing.pricing_rules
        }
        second_prices = {
            (item.min_quantity, item.max_quantity, item.unit_price)
            for item in second.pricing.pricing_rules
        }
        return first_specs == second_specs and first_prices == second_prices
