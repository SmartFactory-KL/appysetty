import os
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import is_dataclass
from pathlib import Path
from typing import Annotated, cast, get_args, get_origin, get_type_hints

import yaml

from appysetty.env import get_env_name
from appysetty.model import (
    AppConfigEntry,
    AppConfigEntryVisitor,
    AppConfigError,
    AppConfigOptions,
    AppConfigSource,
    AppConfigVisitor,
    AppConfigWarning,
)


def read_configuration[T](
    config: type[T] | T,
    sources: AppConfigSource | Sequence[AppConfigSource],
    options: AppConfigOptions | None = None,
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
    if isinstance(sources, AppConfigSource):
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

    for source in sources:
        if source == AppConfigSource.ENV:
            cfg = _read_env(cfg, cfg_type, options)
        elif source == AppConfigSource.YAML:
            cfg = _read_yaml(cfg, cfg_type, options)
        else:
            raise AppConfigError(f"Unsupported source: {source}")

    if options is not None and options.overwrite is not None:
        cfg = _apply_overwrite(cfg, cfg_type, options.overwrite)

    return cast(T, cfg)


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

        visitor(field_name, _type_to_string(field_type), entry)


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

        visitor(field_name, _type_to_string(field_type), field_value)


def _read_env[T](
    config: T, config_type: type[T], options: AppConfigOptions | None
) -> T:
    """Reads the environment while using a possible env_prefix in UPPER_SNAKE_CASE"""
    prefix = options.env_prefix if options is not None else None
    type_hints = get_type_hints(config_type, include_extras=True)

    values: dict[str, object] = {}

    for field_name in type_hints:
        env_name = get_env_name(prefix, field_name)
        val = os.environ.get(env_name, None)

        if val is None:
            continue

        try:
            values[field_name] = _parse_value_from_string(
                val,
                type_hints[field_name],
            )
        except Exception as e:
            raise AppConfigError(f"Failed to parse {env_name} from ENV: {e}") from e

    for field_name in type_hints:
        if field_name not in values:
            values[field_name] = getattr(config, field_name)

    return config_type(**values)


def _read_yaml[T](
    config: T, config_type: type[T], options: AppConfigOptions | None
) -> T:
    """Reads configuration from a flat yaml file"""
    yaml_path = _get_yaml_path(options)

    if yaml_path is None:
        raise AppConfigError("YAML was used as source, but no yaml file was found")

    try:
        with yaml_path.open("r", encoding="utf-8") as file:
            yaml_values: object = yaml.safe_load(file)
    except OSError as e:
        raise AppConfigError(
            f"Failed to read YAML configuration from {yaml_path}: {e}"
        ) from e
    except yaml.YAMLError as e:
        raise AppConfigError(
            f"Failed to parse YAML configuration from {yaml_path}: {e}"
        ) from e

    if yaml_values is None:
        return config

    if not isinstance(yaml_values, Mapping):
        raise AppConfigError(
            f"Expected YAML configuration to contain a mapping, but got {type(yaml_values).__name__}"
        )

    type_hints = get_type_hints(config_type, include_extras=True)
    values: dict[str, object] = {}

    for field_name in type_hints:
        try:
            if field_name not in yaml_values:
                continue

            value = yaml_values[field_name]
            if value is None:
                continue

            values[field_name] = _parse_value(
                yaml_values[field_name], type_hints[field_name]
            )
        except Exception as e:
            raise AppConfigError(f"Failed to parse {field_name} from YAML: {e}") from e

    for field_name in type_hints:
        if field_name not in values:
            values[field_name] = getattr(config, field_name)

    return config_type(**values)


def _apply_overwrite[T](
    config: T, config_type: type[T], overwrites: Mapping[str, str]
) -> T:
    """Uses the string mapping as ENV to write configuration. Intended for testing."""
    type_hints = get_type_hints(config_type, include_extras=True)
    config_fields = {field_name for field_name in type_hints}

    values: dict[str, object] = {}

    for name, value in overwrites.items():
        if name not in config_fields:
            raise AppConfigError(f"Unknown configuration field in overwrite: {name}")

        try:
            values[name] = _parse_value_from_string(
                value,
                type_hints[name],
            )
        except Exception as e:
            raise AppConfigError(f"Failed to parse overwrite for {name}: {e}") from e

    for field_name in type_hints:
        if field_name not in overwrites:
            values[field_name] = getattr(config, field_name)

    return config_type(**values)


def _get_yaml_path(options: AppConfigOptions | None) -> Path | None:
    """Returns either the set yaml_path in options or the first found path for (config)/config.y(a)ml.
    Returns None if no path was found"""
    if options is not None and options.yaml_path is not None:
        return Path(options.yaml_path)

    candidates = (
        Path("config.yaml"),
        Path("config.yml"),
        Path("config", "config.yaml"),
        Path("config", "config.yml"),
    )

    for yaml_path in candidates:
        if yaml_path.is_file():
            return yaml_path

    return None


def _parse_value_from_string(value: str, value_type: object) -> object:
    """Parses a string to either str, int, float or bool. Other types are not supported."""
    if get_origin(value_type) is Annotated:
        value_type = get_args(value_type)[0]

    if value_type is str:
        return value

    if value_type is int:
        return int(value)

    if value_type is float:
        return float(value)

    if value_type is bool:
        normalized = value.lower()
        return normalized in {"true", "1", "yes", "on"}

    raise AppConfigError(f"Unsupported configuration type {value_type}")


def _parse_value(value: object, value_type: object) -> object:
    """Parses more generic input to either str, int, float or bool. Other types are not supported."""
    if get_origin(value_type) is Annotated:
        value_type = get_args(value_type)[0]

    if isinstance(value, str):
        return _parse_value_from_string(value=value, value_type=value_type)

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

    raise AppConfigError(
        f"Invalid value: expected {value_type}, got {type(value).__name__}"
    )


def _get_config_entry(value_type: object) -> AppConfigEntry | None:
    """Returns the AppConfigEntry metadata of a field if it exists"""
    args = get_args(value_type)

    if get_origin(value_type) is not Annotated:
        return None

    for metadata in args[1:]:
        if isinstance(metadata, AppConfigEntry):
            return metadata


def _type_to_string(field_type: object) -> str:
    """Returns a concise string representation of a type."""
    if isinstance(field_type, type):
        return field_type.__name__
    return str(field_type)
