import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

from appysetty import AppConfigSource
from appysetty.env import get_env_name
from appysetty.model import AppConfigError
from appysetty.parse import parse_value, parse_value_from_string


@dataclass(frozen=True)
class EnvSource(AppConfigSource):
    """Uses Environemtn as source while all keys are converted to UPPER_SNAKE_CASE (with an optional PREFIX if supplied)"""

    prefix: str | None = None

    def load(self, config_type_hints):
        values: dict[str, object] = {}

        for field_name in config_type_hints:
            env_name = get_env_name(field_name, self.prefix)
            val = os.environ.get(env_name, None)

            if val is None:
                continue

            try:
                values[field_name] = parse_value_from_string(
                    val,
                    config_type_hints[field_name],
                )
            except Exception as e:
                raise AppConfigError(f"Failed to parse {env_name} from ENV: {e}") from e

        return values


@dataclass(frozen=True)
class DictSource(AppConfigSource):
    """Uses a simple dict[str,str] as input. Keys must match names of config dataclass"""

    input: dict[str, str]

    def load(self, config_type_hints):
        values: dict[str, object] = {}

        for name, value in self.input.items():
            try:
                if name not in config_type_hints:
                    raise AppConfigError(
                        f"Dict key {name} not found in configuration field names"
                    )

                values[name] = parse_value_from_string(
                    value,
                    config_type_hints[name],
                )
            except Exception as e:
                raise AppConfigError(
                    f"Failed to parse overwrite for {name}: {e}"
                ) from e

        return values


@dataclass(frozen=True)
class YamlSource(AppConfigSource):
    """Reads input from YAML file, ignoring non-existing files when required is False.

    If no path is specified, the first file of the following list is used:
    [config.yml, config.yaml, config/config.yml, config.config.yaml]

    If required is True and no file is found, an error is raised.
    """

    path: Path | str | None = None
    required: bool = True

    def load(self, config_type_hints):
        yaml_path: Path | None = None

        if self.path is None:
            candidates = [
                Path("config.yml"),
                Path("config.yaml"),
                Path("config", "config.yml"),
                Path("config", "config.yaml"),
            ]

            for candidate in candidates:
                if candidate.is_file():
                    yaml_path = candidate
                    break

        elif isinstance(self.path, str):
            yaml_path = Path(self.path)
        else:
            yaml_path = self.path

        if yaml_path is None:
            if self.required:
                raise AppConfigError(
                    "YAML was used as required source, but no yaml file was found"
                )
            else:
                return {}

        try:
            with yaml_path.open("r", encoding="utf-8") as file:
                yaml_values: object = yaml.safe_load(file)
        except OSError as e:
            if self.required:
                raise AppConfigError(
                    f"YAML was used as required source, but failed to read YAML configuration from {yaml_path}: {e}"
                )
            else:
                return {}
        except yaml.YAMLError as e:
            # this will raise even when required is off
            # since the file exists but is invalid - that is a different case from the file not existing
            raise AppConfigError(
                f"Failed to parse YAML configuration from {yaml_path}: {e}"
            ) from e

        if yaml_values is None:
            return {}

        if not isinstance(yaml_values, Mapping):
            raise AppConfigError(
                f"Expected YAML configuration to contain a mapping, but got {type(yaml_values).__name__}"
            )

        values: dict[str, object] = {}

        for yaml_key in yaml_values:
            yaml_value = yaml_values[yaml_key]

            if yaml_value is None:
                continue

            if yaml_key not in config_type_hints:
                raise AppConfigError(
                    f"YAML key {yaml_key} not found in configuration field names"
                )

            try:
                values[yaml_key] = parse_value(yaml_value, config_type_hints[yaml_key])
            except Exception as e:
                raise AppConfigError(
                    f"Failed to parse {yaml_key} from YAML: {e}"
                ) from e

        return values


@dataclass(frozen=True)
class TomlSource(AppConfigSource):
    """Reads input from TOML file, ignoring non-existing files when required is False.

    If no path is specified, the first file of the following list is used:
    [config.toml, config/config.toml]

    If required is True and no file is found, an error is raised.
    """

    path: Path | str | None = None
    required: bool = True

    def load(self, config_type_hints):
        toml_path: Path | None = None

        if self.path is None:
            candidates = [
                Path("config.toml"),
                Path("config", "config.toml"),
            ]

            for candidate in candidates:
                if candidate.is_file():
                    toml_path = candidate
                    break

        elif isinstance(self.path, str):
            toml_path = Path(self.path)
        else:
            toml_path = self.path

        if toml_path is None:
            if self.required:
                raise AppConfigError(
                    "TOML was used as required source, but no toml file was found"
                )
            else:
                return {}

        try:
            with toml_path.open("rb") as file:
                toml_values: object = tomllib.load(file)
        except OSError as e:
            if self.required:
                raise AppConfigError(
                    f"TOML was used as required source, but failed to read TOML configuration from {toml_path}: {e}"
                )
            else:
                return {}
        except tomllib.TOMLDecodeError as e:
            raise AppConfigError(
                f"Failed to parse TOML configuration from {toml_path}: {e}"
            ) from e

        values: dict[str, object] = {}

        for toml_key in toml_values:
            toml_value = toml_values[toml_key]

            if toml_value is None:
                continue

            if toml_key not in config_type_hints:
                raise AppConfigError(
                    f"TOML key {toml_key} not found in configuration field names"
                )

            try:
                values[toml_key] = parse_value(toml_value, config_type_hints[toml_key])
            except Exception as e:
                raise AppConfigError(
                    f"Failed to parse {toml_key} from TOML: {e}"
                ) from e

        return values
