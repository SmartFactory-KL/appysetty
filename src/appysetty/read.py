import dataclasses
import warnings
from collections.abc import Sequence
from dataclasses import is_dataclass
from typing import Annotated, Any, cast, get_args, get_origin, get_type_hints

from appysetty.model import (
    AppConfigEntry,
    AppConfigEntryVisitor,
    AppConfigError,
    AppConfigSource,
    AppConfigVisitor,
    AppConfigWarning,
)
from appysetty.parse import type_to_string


def read_configuration[T](
    config: type[T] | T,
    sources: AppConfigSource | Sequence[AppConfigSource] | None = None,
    trim_strings: bool = False,
) -> T:
    """Read application configuration from at least one source

    Sources are read in the provided order, with later values overwriting previous ones.
    If no values are provided the default values of AppConfig will be used.
    Note that ENV will only read UPPER_SNAKE_CASE variants of the name with a prefix as defined.

    Args:
        sources: list of sources to read
        trim_strings: If set to True, all string config values will apply .strip(), removing whitespaces at start and end

    Returns:
        The resulting application configuration

    Raises:
        AppConfigError: whenever the provided value is invalid
    """
    if sources is None:
        sources = []
    elif isinstance(sources, AppConfigSource):
        sources = [sources]

    cfg_type = config if isinstance(config, type) else type(config)

    # the second check makes sure `config` is handled as dataclass later on
    if not is_dataclass(cfg_type) or not is_dataclass(config):
        raise AppConfigError(
            "The provided class or type must be annotated with @dataclass"
        )

    if not sources:
        warnings.warn(
            "No configuration sources defined. This is fine for testing but may be unintentional in production.",
            AppConfigWarning,
            stacklevel=2,
        )

    type_hints = _get_config_type_hints(cfg_type)

    values = {}

    for field in dataclasses.fields(cfg_type):
        if not field.init:
            continue

        if field.default is not dataclasses.MISSING:
            values[field.name] = field.default
        elif field.default_factory is not dataclasses.MISSING:
            values[field.name] = field.default_factory()

    if not isinstance(config, type):
        for field in dataclasses.fields(config):
            if not field.init:
                continue

            values[field.name] = getattr(config, field.name)

    for source in sources:
        next_values = source.load(type_hints, trim_strings)

        unknown_keys = next_values.keys() - type_hints.keys()

        if unknown_keys:
            raise AppConfigError(
                f"{type(source).__name__} returned unknown fields that are not part of configuration "
                f"fields: {', '.join(sorted(unknown_keys))}"
            )

        values.update(next_values)

    try:
        result = cast(T, cfg_type(**values))
    except TypeError as e:
        raise AppConfigError(f"Could not construct {cfg_type.__name__}: {e}") from e

    return result


def visit_config_entries[T](config: Any, visitor: AppConfigEntryVisitor) -> None:
    """Runs the method once for every configuration entry without the actual value. Intended to generate documentation."""
    type_hints = _get_config_type_hints(config)

    for field_name in type_hints:
        field_type = type_hints[field_name]
        entry = _get_config_entry(type_hints[field_name])
        # when no entry is present, still return an "empty" entry
        # so that generated documentation will not simply be missing this entry
        if entry is None:
            entry = AppConfigEntry("")

        if get_origin(field_type) is Annotated:
            field_type = get_args(field_type)[0]

        visitor(field_name, type_to_string(field_type), entry)


def visit_config_strings[T](config: Any, visitor: AppConfigVisitor) -> None:
    """Runs visitor once for every tuple of [key:str, value:str] for the configuration. Masks anything marked with is_secret."""
    type_hints = _get_config_type_hints(config)

    for field_name in type_hints:
        field_metadata = _get_config_entry(type_hints[field_name])
        field_type = type_hints[field_name]
        field_value = str(getattr(config, field_name))

        if field_metadata is not None and field_metadata.is_secret:
            field_value = f"Masked[len:{len(str(field_value))}]"

        if get_origin(field_type) is Annotated:
            field_type = get_args(field_type)[0]

        visitor(field_name, type_to_string(field_type), field_value)


def _get_config_entry(value_type: object) -> AppConfigEntry | None:
    """Returns the AppConfigEntry metadata of a field if it exists"""
    args = get_args(value_type)

    if get_origin(value_type) is not Annotated:
        return None

    for metadata in args[1:]:
        if isinstance(metadata, AppConfigEntry):
            return metadata


def _get_config_type_hints(
    cfg: Any,
) -> dict[str, Any]:
    """Return type hints only for dataclass fields that participate in __init__."""
    if not is_dataclass(cfg):
        raise AppConfigError(
            "the provided class or type must be annotated with @dataclass"
        )

    cfg_type = cfg if isinstance(cfg, type) else type(cfg)
    type_hints = get_type_hints(cfg_type, include_extras=True)

    dataclass_fields = dataclasses.fields(cfg)

    filtered_type_hints: dict[str, Any] = {}
    for dataclass_field in dataclass_fields:
        if dataclass_field.init and dataclass_field.name in type_hints:
            filtered_type_hints[dataclass_field.name] = type_hints[dataclass_field.name]

    return filtered_type_hints
