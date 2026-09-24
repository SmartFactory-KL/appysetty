from dataclasses import dataclass

import pytest

from appysetty import read_configuration
from appysetty.model import AppConfigError, AppConfigWarning
from appysetty.source import DictSource


@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    timeout: float = 5.0


class TestParsing:
    @pytest.mark.parametrize(
        ("field", "value", "expected"),
        [
            ("host", "example.com", "example.com"),
            ("host", "   example.com   ", "example.com"),
            ("port", "9000", 9000),
            ("timeout", "2.5", 2.5),
            ("debug", "   true   ", True),
            ("debug", "  1  ", True),
            ("debug", "true", True),
            ("debug", "1", True),
            ("debug", "yes", True),
            ("debug", "on", True),
            ("debug", "false", False),
            ("debug", "0", False),
            ("debug", "no", False),
            ("debug", "off", False),
        ],
    )
    def test_overwrite_parses_values(self, field, value, expected):
        config = read_configuration(Config, DictSource({field: value}))

        assert getattr(config, field) == expected

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("port", "not-an-int"),
            ("timeout", "not-a-float"),
        ],
    )
    def test_invalid_numeric_overwrite_raises(self, field, value):

        with (
            pytest.raises(
                AppConfigError,
                match=f"Failed to parse overwrite for {field}",
            ),
        ):
            read_configuration(Config, DictSource({field: value}))

    def test_unsupported_type_raises(self):
        @dataclass
        class UnsupportedConfig:
            values: list[str] = None  # type: ignore[assignment]

        with pytest.raises(
            AppConfigError,
            match="Unsupported configuration type",
        ):
            read_configuration(
                UnsupportedConfig,
                DictSource(
                    input={"values": "foo"},
                ),
            )

    def test_config_instance_can_be_passed(self):
        original = Config(
            host="custom-host",
            port=1234,
            debug=True,
            timeout=10.0,
        )

        with pytest.warns(AppConfigWarning, match="No configuration sources"):
            config = read_configuration(original, [])

        assert config == original
