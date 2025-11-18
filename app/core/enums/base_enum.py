"""BaseEnum module.

This module contains the BaseEnum class.

Classes:
    BaseEnum: BaseEnum class.
"""

from enum import Enum
from typing import TypeVar


T = TypeVar("T", bound="BaseEnum")


class BaseEnum(str, Enum):
    """BaseEnum class.

    Contains all the common methods for the enums.

    Attributes:
        get_by_name() -- Get the enum member by name.
        get_by_value() -- Get the enum member by value.
        list() -- Get the list of all the valid enum values.
        is_valid_key() -- Check if the value is valid.
    """

    @classmethod
    def get_by_name(cls: type[T], key: str) -> T | None:
        """Get the enum member by name.

        Args:
            key: The name of the enum to look up.

        Returns:
            The enum member if found, None otherwise.
        """
        for item in cls:
            if key == item.name:
                return item
        return None

    @classmethod
    def get_by_value(cls: type[T], value: str) -> T | None:
        """Get the enum member by value.

        Args:
            value: The value of the enum to look up.

        Returns:
            The enum member if found, None otherwise.
        """
        for item in cls:
            if value == item.value:
                return item
        return None

    @classmethod
    def keys(cls) -> list[str]:
        """Get the list of all the valid enum keys.

        Returns:
            The list of all the valid enum keys.
        """
        return [item.name for item in cls]

    @classmethod
    def values(cls) -> list[str]:
        """Get the list of all the valid enum values.

        Returns:
            The list of all the valid enum values.
        """
        return [item.value for item in cls]

    @classmethod
    def is_valid_key(cls, key: str) -> bool:
        """Check if the value is valid.

        Args:
            key: The key to validate against the enum.

        Returns:
            True if the value is valid, False otherwise.
        """
        return any(key == item.name for item in cls)
