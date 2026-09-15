from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class AppConfigSource(Enum):
    ENV = "env"
    YAML = "yaml"
    TOML = "toml"


class AppConfigError(Exception):
    """Raised when the provided input has invalid content"""


class AppConfigWarning(UserWarning):
    """Warning raised for uncommon use of configuration"""


@dataclass
class AppConfigEntry:
    description: str = ""
    is_secret: bool = False


# AppConfigVisitor
# [field_name, field_type_as_str, masked_field_value]
AppConfigVisitor = Callable[[str, str, str], None]

# AppConfigEntryVisitor
# [field_name, field_type_as_str, entry]
AppConfigEntryVisitor = Callable[[str, str, AppConfigEntry], None]


@dataclass
class AppConfigOptions:
    env_prefix: str | None = None
    """prefix to use to read environment variables. Should be UPPER_SNAKE_CASE."""
    yaml_path: Path | str | None = None
    """Path to read YAML values from. Defaults to ./(config)/config.y(a)ml if not set"""
    overwrite: Mapping[str, str] | None = None
    """Mapping to overwrite any existing values. Mostly useful for testing, not intended for production use"""
