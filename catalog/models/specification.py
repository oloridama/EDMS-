from dataclasses import dataclass, field
from enum import Enum

class SpecificationValueType(Enum):
    TEXT = "text"
    ENUM = "enum"
    NUMBER = "number"
    BOOLEAN = "boolean"
    
@dataclass
class SpecificationType:
    name: str
    value_type: SpecificationValueType
    allowed_values: list[str] = field(default_factory=list)

    def validate_value(
            self, 
            value: str | int | float | bool
        ) -> bool:
        """
        Validates the provided value against the specification type.
            :param value: The value to validate
            :return: True if valid, False otherwise
        """
        if self.value_type == SpecificationValueType.ENUM:
            return isinstance(value, str) and value in self.allowed_values
        elif self.value_type == SpecificationValueType.NUMBER:
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif self.value_type == SpecificationValueType.BOOLEAN:
            return isinstance(value, bool)
        elif self.value_type == SpecificationValueType.TEXT:
            return isinstance(value, str)
        else:
            return False

@dataclass
class Specification:
    type: SpecificationType
    value: str | int | float | bool

    def validate(self) -> bool:
        """
        Validates the specification value against its type.
        Rejects automatically if the value does not conform to the expected type.
        :return: True if valid, False otherwise
        """
        if not self.type:
            raise ValueError("Specification type is not defined.")
        return self.type.validate_value(self.value)