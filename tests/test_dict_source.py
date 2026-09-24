from dataclasses import dataclass

import pytest

from appysetty import read_configuration
from appysetty.model import AppConfigError
from appysetty.source import DictSource


@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    timeout: float = 5.0


class TestReadConfigurationFromDict:
    def test_overwrite(self):
        inputs = {
            "host": "example.com",
            "port": "9000",
            "debug": "true",
            "timeout": "2.5",
        }

        config = read_configuration(Config, DictSource(input=inputs))

        assert config.host == "example.com"
        assert config.port == 9000
        assert config.debug is True
        assert config.timeout == 2.5

    def test_overwrite_unknown_field_raises(self):
        inputs = {"does_not_exist": "value"}

        with pytest.raises(
            AppConfigError,
            match="not found",
        ):
            read_configuration(Config, DictSource(input=inputs))
