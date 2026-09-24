from dataclasses import dataclass

import pytest

from appysetty import EnvSource, read_configuration
from appysetty.env import get_env_name
from appysetty.model import AppConfigError


@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    timeout: float = 5.0


class TestGetEnvName:
    @pytest.mark.parametrize(
        ("prefix", "field_name", "expected"),
        [
            (None, "host", "HOST"),
            ("", "host", "HOST"),
            ("   ", "host", "HOST"),
            ("APP", "host", "APP_HOST"),
            ("APP_", "host", "APP_HOST"),
            ("MY_APP", "database_url", "MY_APP_DATABASE_URL"),
            ("MY_APP_", "database_url", "MY_APP_DATABASE_URL"),
        ],
    )
    def test_get_env_name(self, prefix, field_name, expected):
        assert get_env_name(field_name, prefix) == expected


class TestReadConfigurationFromEnv:
    def test_reads_environment_variables(self, monkeypatch):
        monkeypatch.setenv("HOST", "example.com")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("TIMEOUT", "2.5")

        config = read_configuration(Config, sources=EnvSource())

        assert config.host == "example.com"
        assert config.port == 9000
        assert config.debug is True
        assert config.timeout == 2.5

    def test_environment_uses_defaults_for_missing_values(self, monkeypatch):
        monkeypatch.setenv("HOST", "example.com")

        config = read_configuration(Config, sources=EnvSource())

        assert config.host == "example.com"
        assert config.port == 8080
        assert config.debug is False
        assert config.timeout == 5.0

    def test_environment_prefix(self, monkeypatch):
        monkeypatch.setenv("APP_HOST", "example.com")
        monkeypatch.setenv("APP_PORT", "9000")

        config = read_configuration(Config, sources=EnvSource(prefix="APP"))

        assert config.host == "example.com"
        assert config.port == 9000

    def test_environment_prefix_with_trailing_underscore(self, monkeypatch):
        monkeypatch.setenv("APP_HOST", "example.com")
        monkeypatch.setenv("APP_PORT", "9000")

        config = read_configuration(Config, sources=EnvSource(prefix="APP_"))

        assert config.host == "example.com"
        assert config.port == 9000

    def test_invalid_environment_value_raises_app_config_error(self, monkeypatch):
        monkeypatch.setenv("PORT", "not-an-integer")

        with pytest.raises(AppConfigError, match="Failed to parse PORT"):
            read_configuration(Config, sources=EnvSource())
