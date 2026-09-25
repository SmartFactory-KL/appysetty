from dataclasses import dataclass
from typing import Annotated

import pytest

from appysetty import AppConfigSource, EnvSource
from appysetty.model import AppConfigEntry, AppConfigError, AppConfigWarning
from appysetty.read import (
    read_configuration,
    visit_config_entries,
    visit_config_strings,
)
from appysetty.source import DictSource, YamlSource


@dataclass
class Config:
    host: Annotated[
        str,
        AppConfigEntry(description="The application host"),
    ] = "localhost"
    port: Annotated[int, AppConfigEntry(description="port to run on")] = 8080
    debug: bool = False
    timeout: float = 5.0


class TestReadConfiguration:
    def test_uses_defaults_when_no_sources_are_provided(self):
        with pytest.warns(AppConfigWarning, match="No configuration sources"):
            config = read_configuration(Config, [])

        assert config == Config()

        with pytest.warns(AppConfigWarning, match="No configuration sources"):
            config = read_configuration(Config, None)

        assert config == Config()

    def test_denies_non_dataclass(self):
        # not a dataclass
        class NonDataclassConfig:
            host: str = "localhost"
            password: str = "secret"

        with (
            pytest.raises(AppConfigError),
        ):
            read_configuration(NonDataclassConfig)

    def test_sources_are_applied_in_order(self, monkeypatch, tmp_path):
        @dataclass
        class OrderConfig:
            from_env: str = "not-set"
            from_yaml: str = "not-set"
            from_dict: str = "not-set"

        monkeypatch.setenv("FROM_ENV", "from-env")

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "from_yaml: from-yaml",
            encoding="utf-8",
        )

        config = read_configuration(
            OrderConfig,
            [
                EnvSource(),
                YamlSource(path=config_file, required=True),
                DictSource(input={"from_dict": "from-dict"}),
            ],
        )

        assert config.from_env == "from-env"
        assert config.from_yaml == "from-yaml"
        assert config.from_dict == "from-dict"

    def test_unknown_fields_raise(self):
        @dataclass
        class OrderConfig:
            from_dict: str = "not-set"

        @dataclass(frozen=True)
        class UnknownSource(AppConfigSource):
            def load(self, config_type_hints, trim_strings: bool = False):
                return {"not-in-config": "hello"}

        with pytest.raises(AppConfigError):
            read_configuration(
                OrderConfig,
                [DictSource(input={"from_dict": "from-dict"}), UnknownSource()],
            )


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
