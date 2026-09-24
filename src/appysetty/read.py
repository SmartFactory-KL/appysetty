import warnings
from collections.abc import Sequence
from dataclasses import is_dataclass
from typing import Annotated, cast, get_args, get_origin, get_type_hints

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
) -> T:
    """Read application configuration from at least one source

    Sources are read in the provided order, with later values overwriting previos ones.
    If no values are provided the default values of AppConfig will be used.
    Note that ENV will only read UPPER_SNAKE_CASE variants of the name with a prefix as defined.

    Args:
        sources: list of sources to read

        options: further options like env_prefix and yaml_path and overwrites for tests

    Returns:
        The resulting application configuration

    Raises:
        AppConfigError: whenever the provided value is invalid
    """
    if sources is None:
        sources = []
    elif isinstance(sources, AppConfigSource):
        sources = [sources]

    if isinstance(config, type):
        cfg_type = config
        cfg = config()
    else:
        cfg_type = type(config)
        cfg = config

    if not is_dataclass(cfg):
        raise AppConfigError(
            "the provided config class must be annotated with @dataclass"
        )

    if not sources:
        warnings.warn(
            "No configuration sources defined. This is fine for testing but may be unintentional in production.",
            AppConfigWarning,
            stacklevel=2,
        )

    type_hints = get_type_hints(cfg_type, include_extras=True)

    values = {field_name: getattr(cfg, field_name) for field_name in type_hints}

    for source in sources:
        next_values = source.load(type_hints)

        unknown = next_values.keys() - type_hints.keys()

        if unknown:
            raise AppConfigError(
                f"{type(source).__name__} returned unknown fields that are not part of configuration "
                f"fields: {', '.join(sorted(unknown))}"
            )

        values.update(next_values)

    return cast(T, cfg_type(**values))


def visit_config_entries[T](config: object, visitor: AppConfigEntryVisitor):
    """Runs the method once for every configuration entry without the actual value. Intended to generate documentation."""
    type_hints = get_type_hints(type(config), include_extras=True)

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


def visit_config_strings[T](config: object, visitor: AppConfigVisitor):
    """Runs visitor once for every tuple of [key:str, value:str] for the configuration. Masks anything marked with is_secret."""
    type_hints = get_type_hints(type(config), include_extras=True)

    for field_name in type_hints:
        field_metadata = _get_config_entry(type_hints[field_name])
        field_type = type_hints[field_name]
        field_value = str(getattr(config, field_name))

        if field_metadata is not None and field_metadata.is_secret:
            field_value = f"Masked[len:{len(field_value)}]"

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
