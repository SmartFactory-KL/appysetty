from dataclasses import dataclass
from os import mkdir
from typing import Annotated

import pytest

from appysetty.env import get_env_name
from appysetty.model import (
    AppConfigEntry,
    AppConfigError,
    AppConfigOptions,
    AppConfigSource,
    AppConfigWarning,
)
from appysetty.read import (
    read_configuration,
    visit_config_entries,
    visit_config_strings,
)


@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    timeout: float = 5.0


class TestReadConfiguration:
    def test_uses_defaults_when_no_sources_are_provided(self):
        with pytest.warns(AppConfigWarning, match="No configuration sources"):
            config = read_configuration(Config, [])

        assert config == Config()

    def test_denies_non_dataclass(self):
        # not a dataclass
        class NonDataclassConfig:
            host: str = "localhost"
            password: str = "secret"

        with pytest.raises(AppConfigError):
            read_configuration(NonDataclassConfig, [])

    def test_reads_environment_variables(self, monkeypatch):
        monkeypatch.setenv("HOST", "example.com")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("TIMEOUT", "2.5")

        config = read_configuration(Config, AppConfigSource.ENV)

        assert config.host == "example.com"
        assert config.port == 9000
        assert config.debug is True
        assert config.timeout == 2.5

    def test_environment_uses_defaults_for_missing_values(self, monkeypatch):
        monkeypatch.setenv("HOST", "example.com")

        config = read_configuration(Config, AppConfigSource.ENV)

        assert config.host == "example.com"
        assert config.port == 8080
        assert config.debug is False
        assert config.timeout == 5.0

    def test_environment_prefix(self, monkeypatch):
        monkeypatch.setenv("APP_HOST", "example.com")
        monkeypatch.setenv("APP_PORT", "9000")

        options = AppConfigOptions(env_prefix="APP")

        config = read_configuration(Config, AppConfigSource.ENV, options)

        assert config.host == "example.com"
        assert config.port == 9000

    def test_environment_prefix_with_trailing_underscore(self, monkeypatch):
        monkeypatch.setenv("APP_HOST", "example.com")
        monkeypatch.setenv("APP_PORT", "9000")

        options = AppConfigOptions(env_prefix="APP_")

        config = read_configuration(Config, AppConfigSource.ENV, options)

        assert config.host == "example.com"
        assert config.port == 9000

    def test_invalid_environment_value_raises_app_config_error(self, monkeypatch):
        monkeypatch.setenv("PORT", "not-an-integer")

        with pytest.raises(AppConfigError, match="Failed to parse PORT"):
            read_configuration(Config, AppConfigSource.ENV)

    def test_sources_are_applied_in_order(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HOST", "from-env")
        monkeypatch.setenv("DEBUG", "true")

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
            host: from-yaml
            port: 9000
            """,
            encoding="utf-8",
        )

        options = AppConfigOptions(yaml_path=config_file)

        config = read_configuration(
            Config,
            [AppConfigSource.ENV, AppConfigSource.YAML],
            options,
        )

        assert config.host == "from-yaml"
        assert config.port == 9000
        assert config.debug == True

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

        options = AppConfigOptions(yaml_path=config_file)

        config = read_configuration(Config, AppConfigSource.YAML, options)

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

        options = AppConfigOptions(yaml_path=config_file)

        config = read_configuration(Config, AppConfigSource.YAML, options)

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

        options = AppConfigOptions(yaml_path=str(config_file))

        config = read_configuration(Config, AppConfigSource.YAML, options)

        assert config.port == 9000

    def test_yaml_path_is_none(self):
        options = AppConfigOptions(yaml_path=None)

        with pytest.raises(AppConfigError):
            read_configuration(Config, AppConfigSource.YAML, options)

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

            config = read_configuration(Config, AppConfigSource.YAML)
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

        options = AppConfigOptions(yaml_path=config_file)

        config = read_configuration(Config, AppConfigSource.YAML, options)

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

        options = AppConfigOptions(yaml_path=config_file)

        with pytest.raises(AppConfigError):
            read_configuration(Config, AppConfigSource.YAML, options)

    def test_yaml_missing_path_raises(self):
        options = AppConfigOptions(yaml_path="/does/not/exist/config.yaml")

        with pytest.raises(
            AppConfigError,
        ):
            read_configuration(Config, AppConfigSource.YAML, options)

    def test_yaml_invalid_syntax_raises(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
            host: [this is
            invalid yaml
            """,
            encoding="utf-8",
        )

        options = AppConfigOptions(yaml_path=config_file)

        with pytest.raises(AppConfigError):
            read_configuration(Config, AppConfigSource.YAML, options)

    def test_yaml_requires_mapping(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
            - one
            - two
            """,
            encoding="utf-8",
        )

        options = AppConfigOptions(yaml_path=config_file)

        with pytest.raises(
            AppConfigError,
        ):
            read_configuration(Config, AppConfigSource.YAML, options)

    def test_empty_yaml_uses_defaults(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("", encoding="utf-8")

        options = AppConfigOptions(yaml_path=config_file)

        config = read_configuration(Config, AppConfigSource.YAML, options)

        assert config == Config()

    def test_overwrite(self):
        options = AppConfigOptions(
            overwrite={
                "host": "example.com",
                "port": "9000",
                "debug": "true",
                "timeout": "2.5",
            }
        )

        with pytest.warns(AppConfigWarning, match="No configuration sources"):
            config = read_configuration(Config, [], options)

        assert config.host == "example.com"
        assert config.port == 9000
        assert config.debug is True
        assert config.timeout == 2.5

    def test_overwrite_takes_precedence_over_environment(self, monkeypatch):
        monkeypatch.setenv("HOST", "from-env")

        options = AppConfigOptions(
            overwrite={"host": "from-overwrite"},
        )

        config = read_configuration(
            Config,
            AppConfigSource.ENV,
            options,
        )

        assert config.host == "from-overwrite"

    def test_overwrite_takes_precedence_over_yaml(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "host: from-yaml",
            encoding="utf-8",
        )

        options = AppConfigOptions(
            yaml_path=config_file,
            overwrite={"host": "from-overwrite"},
        )

        config = read_configuration(
            Config,
            AppConfigSource.YAML,
            options,
        )

        assert config.host == "from-overwrite"

    def test_overwrite_unknown_field_raises(self):
        options = AppConfigOptions(
            overwrite={"does_not_exist": "value"},
        )

        with (
            pytest.raises(
                AppConfigError,
                match="Unknown configuration field in overwrite",
            ),
            pytest.warns(AppConfigWarning, match="No configuration sources"),
        ):
            read_configuration(Config, [], options)

    # TODO: Add TOML tests once it is added
    def test_unsupported_source_raises(self):
        with pytest.raises(AppConfigError, match="Unsupported source"):
            # TOML is deliberately not implemented.
            read_configuration(Config, AppConfigSource.TOML)


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
        assert get_env_name(prefix, field_name) == expected


class TestAnnotatedConfig:
    @dataclass
    class ConfigWithMetadata:
        host: Annotated[
            str,
            AppConfigEntry(description="The application host"),
        ] = "localhost"

        password: Annotated[
            str,
            AppConfigEntry(description="The database password", is_secret=True),
        ] = "secret"

    def test_reads_environment_variables(self, monkeypatch):
        monkeypatch.setenv("HOST", "example.com")
        monkeypatch.setenv("PASSWORD", "9000")

        config = read_configuration(self.ConfigWithMetadata(), AppConfigSource.ENV)

        assert config.host == "example.com"
        assert config.password == "9000"

    def test_yaml_source(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
            host: "example.com"
            password: "9000"
            """,
            encoding="utf-8",
        )

        options = AppConfigOptions(yaml_path=config_file)

        config = read_configuration(
            self.ConfigWithMetadata(), AppConfigSource.YAML, options
        )

        assert config.host == "example.com"
        assert config.password == "9000"

    def test_visit_config_entries(self):
        config = self.ConfigWithMetadata()
        entries = {}

        visit_config_entries(
            config,
            lambda name, field_type, entry: entries.__setitem__(name, entry),
        )

        assert entries == {
            "host": AppConfigEntry("The application host"),
            "password": AppConfigEntry(
                "The database password",
                is_secret=True,
            ),
        }

    def test_visit_config_entries_returns_correct_type(self):
        @dataclass
        class Config:
            host: Annotated[
                str,
                AppConfigEntry("The host"),
            ] = "localhost"
            port: int = 8080

        values = {}

        visit_config_entries(
            Config(),
            lambda name, field_type, value: values.__setitem__(name, field_type),
        )

        assert values == {
            "host": "str",
            "port": "int",
        }

    def test_visit_config_entries_zeroes_fields_without_metadata(self):
        @dataclass
        class Config:
            host: Annotated[
                str,
                AppConfigEntry("The host"),
            ] = "localhost"
            port: int = 8080

        entries = {}

        visit_config_entries(
            Config(),
            lambda name, field_type, entry: entries.__setitem__(name, entry),
        )

        assert entries == {
            "port": AppConfigEntry(""),
            "host": AppConfigEntry("The host"),
        }

    def test_visit_config_strings(self):
        config = self.ConfigWithMetadata()
        values = {}

        visit_config_strings(
            config,
            lambda name, field_type, value: values.__setitem__(name, value),
        )

        assert values["host"] == "localhost"
        assert values["password"] == "Masked[len:6]"

    def test_visit_config_strings_includes_unannotated_fields(self):
        @dataclass
        class Config:
            host: Annotated[
                str,
                AppConfigEntry("The host"),
            ] = "localhost"
            port: int = 8080

        values = {}

        visit_config_strings(
            Config(),
            lambda name, field_type, value: values.__setitem__(name, value),
        )

        assert values == {
            "host": "localhost",
            "port": "8080",
        }

    def test_visit_config_strings_returns_correct_type(self):
        @dataclass
        class Config:
            host: Annotated[
                str,
                AppConfigEntry("The host"),
            ] = "localhost"
            port: int = 8080

        values = {}

        visit_config_strings(
            Config(),
            lambda name, field_type, value: values.__setitem__(name, field_type),
        )

        assert values == {
            "host": "str",
            "port": "int",
        }

    def test_visit_config_strings_masks_secret(self):
        @dataclass
        class Config:
            password: Annotated[
                str,
                AppConfigEntry("Password", is_secret=True),
            ] = "super-secret"

        values = {}

        visit_config_strings(
            Config(),
            lambda name, field_type, value: values.__setitem__(name, value),
        )

        assert values["password"] == "Masked[len:12]"
        assert "super-secret" not in values["password"]


class TestParsing:
    @pytest.mark.parametrize(
        ("field", "value", "expected"),
        [
            ("host", "example.com", "example.com"),
            ("port", "9000", 9000),
            ("timeout", "2.5", 2.5),
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
        options = AppConfigOptions(
            overwrite={field: value},
        )

        with pytest.warns(AppConfigWarning, match="No configuration sources"):
            config = read_configuration(Config, [], options)

        assert getattr(config, field) == expected

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("port", "not-an-int"),
            ("timeout", "not-a-float"),
        ],
    )
    def test_invalid_numeric_overwrite_raises(self, field, value):
        options = AppConfigOptions(
            overwrite={field: value},
        )

        with (
            pytest.raises(
                AppConfigError,
                match=f"Failed to parse overwrite for {field}",
            ),
            pytest.warns(AppConfigWarning, match="No configuration sources"),
        ):
            read_configuration(Config, [], options)

    def test_unsupported_type_raises(self):
        @dataclass
        class UnsupportedConfig:
            values: list[str] = None  # type: ignore[assignment]

        options = AppConfigOptions(
            overwrite={"values": "foo"},
        )

        with (
            pytest.raises(
                AppConfigError,
                match="Unsupported configuration type",
            ),
            pytest.warns(AppConfigWarning, match="No configuration sources"),
        ):
            read_configuration(UnsupportedConfig, [], options)

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
