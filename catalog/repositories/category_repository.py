from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from catalog.models.category import Category
from catalog.repositories.mappers import category_from_record
from catalog.repositories.records import CategoryRecord, ProductRecord, SpecificationTypeRecord
from shared.error_handling import CategoryAlreadyExistsError


class CategoryRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def save_category(self, category: Category) -> int:
        record = CategoryRecord(
            name=category.name,
            description=category.description,
            specification_types=[
                SpecificationTypeRecord(
                    name=specification_type.name,
                    value_type=specification_type.value_type.value,
                    allowed_values=specification_type.allowed_values,
                )
                for specification_type in category.specification_types
            ],
        )
        self.db_session.add(record)
        try:
            self.db_session.flush()
        except IntegrityError as error:
            self.db_session.rollback()
            raise CategoryAlreadyExistsError(category.name) from error
        return record.id

    def category_exists(self, category_name: str) -> tuple[bool, Category | None]:
        statement = (
            select(CategoryRecord)
            .options(selectinload(CategoryRecord.specification_types))
            .where(CategoryRecord.name == category_name)
        )
        record = self.db_session.scalar(statement)
        return (record is not None, category_from_record(record) if record else None)

    def check_product_category(self, product_name: str) -> Category | None:
        statement = (
            select(ProductRecord)
            .options(selectinload(ProductRecord.category))
            .where(ProductRecord.name == product_name)
        )
        product = self.db_session.scalar(statement)
        return category_from_record(product.category) if product else None

    @staticmethod
    def find_category(categories: list[Category], category_name: str) -> Category | None:
        return next((category for category in categories if category.name == category_name), None)
