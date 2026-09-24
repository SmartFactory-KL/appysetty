from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass


class AppConfigSource(ABC):
    """Represents any source, which only provide a load method"""

    @abstractmethod
    def load(
        self, config_type_hints: Mapping[str, object], trim_strings: bool = False
    ) -> Mapping[str, object]: ...


class AppConfigError(Exception):
    """Raised when the provided input has invalid content"""


class AppConfigWarning(UserWarning):
    """Warning raised for uncommon use of configuration"""


@dataclass(frozen=True)
class AppConfigEntry:
    description: str = ""
    is_secret: bool = False


# AppConfigVisitor
# [field_name, field_type_as_str, masked_field_value]
AppConfigVisitor = Callable[[str, str, str], None]

# AppConfigEntryVisitor
# [field_name, field_type_as_str, entry]
AppConfigEntryVisitor = Callable[[str, str, AppConfigEntry], None]
