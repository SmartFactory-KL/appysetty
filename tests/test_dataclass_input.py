from dataclasses import dataclass, field

import pytest

from appysetty import AppConfigError, AppConfigWarning, DictSource, read_configuration

# --- Test configs -----------------------------------------------------------


@dataclass
class RequiredConfig:
    host: str
    port: int


@dataclass
class DefaultConfig:
    host: str = "localhost"
    port: int = 8080


@dataclass
class MixedConfig:
    host: str
    port: int = 8080


@dataclass
class DerivedConfig:
    host: str
    port: int = 8080
    url: str = field(init=False)

    def __post_init__(self):
        self.url = f"http://{self.host}:{self.port}"


@dataclass
class FactoryConfig:
    tags: list[str] = field(default_factory=list)


class NotAConfig:
    pass


# --- Tests ------------------------------------------------------------------
DefaultDictSource = DictSource(
    {
        "host": "localhost",
        "port": "8080",
    }
)


def test_accepts_dataclass_class():
    config = read_configuration(
        RequiredConfig,
        sources=DefaultDictSource,  # source providing host and port
    )

    assert isinstance(config, RequiredConfig)


def test_accepts_dataclass_instance():
    original = RequiredConfig(host="localhost", port=8080)

    with pytest.warns(AppConfigWarning):
        config = read_configuration(original)

    assert isinstance(config, RequiredConfig)
    assert config.host == "localhost"
    assert config.port == 8080


def test_instance_is_copied_not_returned():
    original = DefaultConfig(host="example.com", port=1234)

    with pytest.warns(AppConfigWarning):
        config = read_configuration(original)

    assert config is not original
    assert config == original


def test_class_does_not_need_zero_argument_constructor():
    config = read_configuration(
        RequiredConfig,
        sources=DefaultDictSource,  # providing both required fields
    )

    assert config.host == "localhost"
    assert config.port == 8080


def test_class_defaults_are_used():
    with pytest.warns(AppConfigWarning):
        config = read_configuration(DefaultConfig)

    assert config.host == "localhost"
    assert config.port == 8080


def test_instance_values_override_class_defaults():
    original = DefaultConfig(
        host="example.com",
        port=9000,
    )

    with pytest.warns(AppConfigWarning):
        config = read_configuration(original)

    assert config.host == "example.com"
    assert config.port == 9000


def test_required_field_without_default_is_missing():
    with pytest.raises(AppConfigError), pytest.warns(AppConfigWarning):
        read_configuration(RequiredConfig)


def test_init_false_field_is_not_treated_as_input():
    config = read_configuration(
        DerivedConfig,
        sources=DefaultDictSource,
    )

    assert config.url == f"http://{config.host}:{config.port}"


def test_default_factory_is_used():
    with pytest.warns(AppConfigWarning):
        config = read_configuration(FactoryConfig)

    assert config.tags == []


def test_dataclass_class_with_required_fields_does_not_need_zero_arg_constructor():
    @dataclass
    class Config:
        host: str
        port: int

    config = read_configuration(
        Config,
        sources=DictSource({"host": "example.com", "port": "443"}),
    )

    assert config.host == "example.com"
    assert config.port == 443


def test_dataclass_class_with_missing_values_raises():
    @dataclass
    class Config:
        host: str
        port: int

    with pytest.raises(AppConfigError), pytest.warns(AppConfigWarning):
        read_configuration(
            Config,
        )


def test_rejects_non_dataclass_class():
    with pytest.raises(AppConfigError):
        read_configuration(NotAConfig)


def test_rejects_non_dataclass_instance():
    with pytest.raises(AppConfigError):
        read_configuration(NotAConfig())
