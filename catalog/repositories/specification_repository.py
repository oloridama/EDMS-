from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from catalog.models.category import Category
from catalog.models.specification import Specification, SpecificationType, SpecificationValueType
from catalog.repositories.mappers import category_from_record
from catalog.repositories.records import (
    CategoryRecord,
    SpecificationTypeRecord,
    SpecificationValueRecord,
)
from shared.error_handling import SpecificationAlreadyExistsError


class SpecificationRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def save_specification(self, specification: Specification, category: Category) -> int:
        category_record = self.db_session.scalar(
            select(CategoryRecord)
            .options(selectinload(CategoryRecord.specification_types))
            .where(CategoryRecord.name == category.name)
        )
        if category_record is None:
            raise ValueError(f"Category '{category.name}' was not found.")

        type_record = next(
            (
                item
                for item in category_record.specification_types
                if item.name == specification.type.name
            ),
            None,
        )
        if type_record is None:
            raise ValueError(
                f"Specification type '{specification.type.name}' is not required "
                f"by category '{category.name}'."
            )

        existing_records = self.db_session.scalars(
            select(SpecificationValueRecord).where(
                SpecificationValueRecord.category_id == category_record.id,
                SpecificationValueRecord.specification_type_id == type_record.id,
            )
        ).all()
        if any(item.value == specification.value for item in existing_records):
            raise SpecificationAlreadyExistsError(
                category.name,
                specification.type.name,
                specification.value,
            )

        record = SpecificationValueRecord(
            category_id=category_record.id,
            specification_type_id=type_record.id,
            value=specification.value,
        )
        self.db_session.add(record)
        self.db_session.flush()
        return record.id

    def get_specifications(self) -> list[Specification]:
        records = self.db_session.scalars(
            select(SpecificationValueRecord).options(
                selectinload(SpecificationValueRecord.specification_type)
            )
        ).all()
        return [self._to_domain(record) for record in records]

    def get_specifications_by_category(self, category: Category) -> list[Specification]:
        category_record = self.db_session.scalar(
            select(CategoryRecord).where(CategoryRecord.name == category.name)
        )
        if category_record is None:
            return []
        records = self.db_session.scalars(
            select(SpecificationValueRecord)
            .options(selectinload(SpecificationValueRecord.specification_type))
            .where(SpecificationValueRecord.category_id == category_record.id)
        ).all()
        return [self._to_domain(record) for record in records]

    @staticmethod
    def _to_domain(record: SpecificationValueRecord) -> Specification:
        type_record = record.specification_type
        return Specification(
            type=SpecificationType(
                name=type_record.name,
                value_type=SpecificationValueType(type_record.value_type),
                allowed_values=type_record.allowed_values or [],
            ),
            value=record.value,
        )
