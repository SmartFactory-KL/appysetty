from dataclasses import dataclass
from os import mkdir

import pytest

from appysetty import TomlSource, read_configuration
from appysetty.model import AppConfigError


@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    timeout: float = 5.0


class TestReadConfigurationFromTOML:
    def test_toml_source(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
            host = "example.com"
            port = 9000
            debug = true
            timeout = 2.5
            """,
            encoding="utf-8",
        )

        config = read_configuration(Config, TomlSource(config_file))

        assert config.host == "example.com"
        assert config.port == 9000
        assert config.debug is True
        assert config.timeout == 2.5

    def test_toml_uses_defaults_for_missing_values(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'host = "example.com"',
            encoding="utf-8",
        )

        config = read_configuration(Config, TomlSource(config_file))

        assert config.host == "example.com"
        assert config.port == 8080
        assert config.debug is False
        assert config.timeout == 5.0

    def test_toml_path_can_be_string(self, tmp_path):
        config_file = tmp_path / "config_test.toml"
        config_file.write_text(
            "port = 9000",
            encoding="utf-8",
        )

        config = read_configuration(Config, TomlSource(config_file))

        assert config.port == 9000

    def test_toml_path_is_none(self):
        toml_path = None

        with pytest.raises(AppConfigError):
            read_configuration(Config, TomlSource(toml_path))

    def test_toml_path_defaults(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        variants = [
            "config.toml",
            "config/config.toml",
        ]

        mkdir(tmp_path / "config")

        for variant in variants:
            (tmp_path / variant).write_text("port = 9000\n")

            config = read_configuration(Config, TomlSource())
            assert config.port == 9000

    def test_toml_raises_for_invalid_type(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
            host = "example.com"
            port = []
            """,
            encoding="utf-8",
        )

        with pytest.raises(AppConfigError):
            read_configuration(Config, TomlSource(config_file))

    def test_toml_raises_for_invalid_key(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
            non_existing = "example.com"
            port = []
            """,
            encoding="utf-8",
        )

        with pytest.raises(AppConfigError):
            read_configuration(Config, TomlSource(config_file))

    def test_toml_missing_path_raises(self):
        toml_path = "/does/not/exist/config.toml"

        with pytest.raises(AppConfigError):
            read_configuration(
                Config,
                TomlSource(toml_path, required=True),
            )

    def test_toml_invalid_syntax_raises(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
            host = "example.com
            port = 9000
            """,
            encoding="utf-8",
        )

        with pytest.raises(AppConfigError):
            read_configuration(Config, TomlSource(config_file))

    def test_toml_requires_mapping(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
            one
            two
            """,
            encoding="utf-8",
        )

        with pytest.raises(AppConfigError):
            read_configuration(Config, TomlSource(config_file))

    def test_empty_toml_uses_defaults(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text("", encoding="utf-8")

        config = read_configuration(Config, TomlSource(config_file))

        assert config == Config()
