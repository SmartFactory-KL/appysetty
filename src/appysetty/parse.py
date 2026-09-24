from typing import Annotated, get_args, get_origin

from appysetty.model import AppConfigError


def parse_value_from_string(value: str, value_type: object) -> object:
    """Parses a string to either str, int, float or bool. Other types are not supported."""
    if get_origin(value_type) is Annotated:
        value_type = get_args(value_type)[0]

    trimmed = value.strip()

    if value_type is str:
        return trimmed

    if value_type is int:
        return int(trimmed)

    if value_type is float:
        return float(trimmed)

    if value_type is bool:
        normalized = trimmed.lower()
        return normalized in {"true", "1", "yes", "on"}

    raise AppConfigError(f"Unsupported configuration type {value_type}")


def parse_value(value: object, value_type: object) -> object:
    """Parses more generic input to either str, int, float or bool. Other types are not supported."""
    if get_origin(value_type) is Annotated:
        value_type = get_args(value_type)[0]

    if isinstance(value, str):
        return parse_value_from_string(value=value, value_type=value_type)

    if value_type is int and isinstance(value, int) and not isinstance(value, bool):
        return value

    if (
        value_type is float
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
    ):
        return float(value)

    if value_type is bool and isinstance(value, bool):
        return value

    if value_type is bool and isinstance(value, int):
        if value == 0:
            return False
        elif value == 1:
            return True

    raise AppConfigError(
        f"Invalid value: expected {value_type}, got {type(value).__name__}"
    )


def type_to_string(field_type: object) -> str:
    """Returns a concise string representation of a type."""
    if isinstance(field_type, type):
        return field_type.__name__
    return str(field_type)
