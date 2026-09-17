from catalog.models.specification import Specification, SpecificationType, SpecificationValueType

def test_specification_validation():
    # Create a SpecificationType for ENUM
    enum_spec_type = SpecificationType(
        name="Color",
        value_type=SpecificationValueType.ENUM,
        allowed_values=["Red", "Green", "Blue"]
    )

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

    # Create a Specification with a valid BOOLEAN value
    valid_boolean_spec = Specification(type=boolean_spec_type, value=True)
    assert valid_boolean_spec.validate() == True

    # Create a Specification with an invalid BOOLEAN value (string)
    invalid_boolean_spec = Specification(type=boolean_spec_type, value="true")
    assert invalid_boolean_spec.validate() == False

if __name__ == "__main__":
    test_specification_validation()
    print("All tests passed.")