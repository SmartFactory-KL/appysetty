from appysetty.model import (
    AppConfigEntry,
)


def test_entry_defaults():
    entry = AppConfigEntry("A description")

    assert entry.description == "A description"
    assert entry.is_secret is False


def test_entry_secret():
    entry = AppConfigEntry("A secret", is_secret=True)

    assert entry.description == "A secret"
    assert entry.is_secret is True
