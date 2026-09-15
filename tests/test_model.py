from appysetty.model import (
    AppConfigEntry,
    AppConfigOptions,
    AppConfigSource,
)


def test_sources():
    assert AppConfigSource.ENV.value == "env"
    assert AppConfigSource.YAML.value == "yaml"
    assert AppConfigSource.TOML.value == "toml"


def test_entry_defaults():
    entry = AppConfigEntry("A description")

    assert entry.description == "A description"
    assert entry.is_secret is False


def test_entry_secret():
    entry = AppConfigEntry("A secret", is_secret=True)

    assert entry.description == "A secret"
    assert entry.is_secret is True


def test_options_defaults():
    options = AppConfigOptions()

    assert options.env_prefix is None
    assert options.yaml_path is None
    assert options.overwrite is None
