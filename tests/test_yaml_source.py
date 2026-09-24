from dataclasses import dataclass
from os import mkdir

import pytest

from appysetty import YamlSource, read_configuration
from appysetty.model import AppConfigError


@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    timeout: float = 5.0


class TestReadConfigurationFromYAML:
    def test_yaml_source(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
            host: example.com
            port: 9000
            debug: true
            timeout: 2.5
            """,
            encoding="utf-8",
        )

        config = read_configuration(Config, YamlSource(config_file))

        assert config.host == "example.com"
        assert config.port == 9000
        assert config.debug is True
        assert config.timeout == 2.5

    def test_yaml_uses_defaults_for_missing_values(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "host: example.com",
            encoding="utf-8",
        )

        config = read_configuration(Config, YamlSource(config_file))

        assert config.host == "example.com"
        assert config.port == 8080
        assert config.debug is False
        assert config.timeout == 5.0

    def test_yaml_path_can_be_string(self, tmp_path):
        config_file = tmp_path / "config_test.yaml"
        config_file.write_text(
            "port: 9000",
            encoding="utf-8",
        )

        config = read_configuration(Config, YamlSource(config_file))

        assert config.port == 9000

    def test_yaml_path_is_none(self):
        yaml_path = None

        with pytest.raises(AppConfigError):
            read_configuration(Config, YamlSource(yaml_path))

    def test_yaml_path_defaults(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        variants = [
            "config.yml",
            "config.yaml",
            "config/config.yml",
            "config/config.yaml",
        ]

        mkdir(tmp_path / "config")

        for variant in variants:
            (tmp_path / variant).write_text("port: 9000\n")

            config = read_configuration(Config, YamlSource())
            assert config.port == 9000

    def test_yaml_skips_none_values(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
            host: example.com
            port:
            """,
            encoding="utf-8",
        )

        config = read_configuration(Config, YamlSource(config_file))

        assert config.host == "example.com"
        assert config.port == 8080
        assert config.debug is False
        assert config.timeout == 5.0

    def test_yaml_raises_for_invalid_type(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
            host: example.com
            port: []
            """,
            encoding="utf-8",
        )

        with pytest.raises(AppConfigError):
            read_configuration(Config, YamlSource(config_file))

    def test_yaml_raises_for_invalid_key(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
            non_existing: example.com
            port: []
            """,
            encoding="utf-8",
        )

        with pytest.raises(AppConfigError):
            read_configuration(Config, YamlSource(config_file))

    def test_yaml_missing_path_raises(self):
        yaml_path = "/does/not/exist/config.yaml"

        with pytest.raises(
            AppConfigError,
        ):
            read_configuration(Config, YamlSource(yaml_path, required=True))

    def test_yaml_invalid_syntax_raises(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
            host: [this is
            invalid yaml
            """,
            encoding="utf-8",
        )

        with pytest.raises(AppConfigError):
            read_configuration(Config, YamlSource(config_file))

    def test_yaml_requires_mapping(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
            - one
            - two
            """,
            encoding="utf-8",
        )

        with pytest.raises(AppConfigError):
            read_configuration(Config, YamlSource(config_file))

    def test_empty_yaml_uses_defaults(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("", encoding="utf-8")

        config = read_configuration(Config, YamlSource(config_file))

        assert config == Config()
