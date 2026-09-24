from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from appysetty import AppConfigEntry
from appysetty.write import (
    _encase_str_in_quotes,
    write_config_markdown,
    write_config_yaml_example,
    write_configuration_documentation,
)


@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    enabled: bool = True
    password: Annotated[str, AppConfigEntry(is_secret=True)] = "MyPassword"


def test_encase_str_in_quotes():
    assert _encase_str_in_quotes("hello") == '"hello"'
    assert _encase_str_in_quotes(123) == "123"
    assert _encase_str_in_quotes(True) == "True"


def test_write_config_yaml_example(tmp_path: Path):
    write_config_yaml_example(Config(), output_dir=tmp_path)

    output = (tmp_path / "config.example.yaml").read_text()

    assert "# Type: str" in output
    assert "# Type: int" in output
    assert "# Type: bool" in output

    assert 'host: "localhost"' in output
    assert "port: 8080" in output
    assert "enabled: True" in output

    assert "MyPassword" not in output


def test_write_config_yaml_example_accepts_config_type(tmp_path: Path):
    write_config_yaml_example(Config, output_dir=tmp_path)

    output = (tmp_path / "config.example.yaml").read_text()

    assert 'host: "localhost"' in output
    assert "port: 8080" in output
    assert "enabled: True" in output


def test_write_config_markdown(tmp_path: Path):
    write_config_markdown(
        Config(),
        env_prefix="APP",
        output_dir=tmp_path,
    )

    output = (tmp_path / "DefaultConfiguration.md").read_text()

    assert "# Application Configuration" in output
    assert "| ENV | Variable | Type | Default | Is Secret | Description |" in output

    assert "| APP_HOST | host | str | localhost |" in output
    assert "| APP_PORT | port | int | 8080 |" in output
    assert "| APP_ENABLED | enabled | bool | True |" in output

    assert "MyPassword" not in output


def test_write_config_markdown_without_env_prefix(tmp_path: Path):
    write_config_markdown(Config(), output_dir=tmp_path)

    output = (tmp_path / "DefaultConfiguration.md").read_text()

    assert "| HOST | host |" in output
    assert "| PORT | port |" in output
    assert "| ENABLED | enabled |" in output


def test_write_config_markdown_accepts_config_type(tmp_path: Path):
    write_config_markdown(
        Config,
        env_prefix="APP",
        output_dir=tmp_path,
    )

    output = (tmp_path / "DefaultConfiguration.md").read_text()

    assert "| APP_HOST | host | str | localhost |" in output


def test_write_config_markdown_contains_docker_compose(tmp_path: Path):
    write_config_markdown(
        Config(),
        env_prefix="APP",
        output_dir=tmp_path,
    )

    output = (tmp_path / "DefaultConfiguration.md").read_text()

    assert "## Docker Compose" in output
    assert "environment:" in output
    assert "  APP_HOST: localhost" in output
    assert "  APP_PORT: 8080" in output
    assert "  APP_ENABLED: True" in output

    assert "MyPassword" not in output


def test_write_config_markdown_contains_docker_run(tmp_path: Path):
    write_config_markdown(
        Config(),
        env_prefix="APP",
        output_dir=tmp_path,
    )

    output = (tmp_path / "DefaultConfiguration.md").read_text()

    assert "## Docker Run" in output
    assert "docker run \\" in output

    assert "  -e APP_HOST=localhost \\" in output
    assert "  -e APP_PORT=8080 \\" in output
    assert "  -e APP_ENABLED=True" in output

    assert "  your-image:latest" in output

    assert "MyPassword" not in output


def test_write_config_documentation_creates_both_files(tmp_path: Path):
    write_configuration_documentation(
        Config(),
        env_prefix="APP",
        output_dir=tmp_path,
    )

    assert (tmp_path / "config.example.yaml").exists()
    assert (tmp_path / "DefaultConfiguration.md").exists()


def test_write_config_markdown_creates_output_directory(tmp_path: Path):
    output_dir = tmp_path / "nested" / "config"

    write_config_markdown(Config(), output_dir=output_dir)

    assert (output_dir / "DefaultConfiguration.md").exists()


def test_write_config_yaml_example_creates_output_directory(tmp_path: Path):
    output_dir = tmp_path / "nested" / "config"

    write_config_yaml_example(Config(), output_dir=output_dir)

    assert (output_dir / "config.example.yaml").exists()
