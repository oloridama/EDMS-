from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import catalog.repositories.records
from catalog.models.category import Category
from catalog.models.specification import Specification, SpecificationType, SpecificationValueType
from catalog.repositories.category_repository import CategoryRepository
from catalog.repositories.specification_repository import SpecificationRepository
from catalog.services.category_service import CategoryService
from catalog.services.specification_service import SpecificationService
from shared.database import Base
from shared.error_handling import SpecificationAlreadyExistsError


def make_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)

def test_specification_validation():
    # Create a SpecificationType for ENUM
    enum_spec_type = SpecificationType(
        name="Color",
        value_type=SpecificationValueType.ENUM,
        allowed_values=["Red", "Green", "Blue"]
    )

    # Test the type rules directly
    assert enum_spec_type.validate_value("Red") is True
    assert enum_spec_type.validate_value("Yellow") is False

    # Test the specification public behavior
    # Create a Specification with a valid ENUM value
    valid_enum_spec = Specification(type=enum_spec_type, value="Red")
    assert valid_enum_spec.validate() == True

    # Create a Specification with an invalid ENUM value
    invalid_enum_spec = Specification(type=enum_spec_type, value="Yellow")
    assert invalid_enum_spec.validate() == False

    # Create a SpecificationType for NUMBER
    number_spec_type = SpecificationType(
        name="Weight",
        value_type=SpecificationValueType.NUMBER
    )

    assert number_spec_type.validate_value(10) is True
    assert number_spec_type.validate_value(10.5) is True
    assert number_spec_type.validate_value("ten") is False

    # Create a Specification with a valid NUMBER value
    valid_number_spec = Specification(type=number_spec_type, value=10.5)
    assert valid_number_spec.validate() == True

    # Create a Specification with an invalid NUMBER value (string)
    invalid_number_spec = Specification(type=number_spec_type, value="ten")
    assert invalid_number_spec.validate() == False

    # Create a SpecificationType for BOOLEAN
    boolean_spec_type = SpecificationType(
        name="IsAvailable",
        value_type=SpecificationValueType.BOOLEAN
    )
    assert boolean_spec_type.validate_value(True) is True
    assert boolean_spec_type.validate_value(False) is True
    assert boolean_spec_type.validate_value("true") is False

    # Create a Specification with a valid BOOLEAN value
    valid_boolean_spec = Specification(type=boolean_spec_type, value=True)
    assert valid_boolean_spec.validate() == True

    # Create a Specification with an invalid BOOLEAN value (string)
    invalid_boolean_spec = Specification(type=boolean_spec_type, value="true")
    assert invalid_boolean_spec.validate() == False

def test_category_creation_requires_specifications():
    session = make_session()
    category_repo = CategoryRepository(session)
    spec_repo = SpecificationRepository(session)
    service = CategoryService(category_repo, SpecificationService(spec_repo))

    try:
        service.create_category("Electronics", None)
    except ValueError as error:
        assert "specification" in str(error).lower()
    else:
        raise AssertionError("Expected ValueError for category creation without specifications.")
    finally:
        session.close()


def test_category_and_repository_stay_in_sync():
    session = make_session()
    specification_type = SpecificationType(
        name="Weight",
        value_type=SpecificationValueType.NUMBER,
    )
    category = Category(name="Furniture", specification_types=[specification_type])
    spec = Specification(
        type=specification_type,
        value=10.5,
    )
    CategoryRepository(session).save_category(category)
    repo = SpecificationRepository(session)
    repo.save_specification(spec, category)

    assert repo.get_specifications_by_category(category) == [spec]

    try:
        repo.save_specification(spec, category)
    except SpecificationAlreadyExistsError as error:
        assert error.specification_type == "Weight"
    else:
        raise AssertionError("Expected SpecificationAlreadyExistsError for a duplicate value.")
    finally:
        session.close()


if __name__ == "__main__":
    test_specification_validation()
    test_category_creation_requires_specifications()
    test_category_and_repository_stay_in_sync()
    print("All tests passed.")