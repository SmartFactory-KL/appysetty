import shlex
from dataclasses import dataclass
from pathlib import Path

import yaml

from appysetty.env import get_env_name
from appysetty.model import AppConfigEntry
from appysetty.read import visit_config_entries


@dataclass
class MarkdownInfoEntry:
    env_name: str
    field_name: str
    field_type: str
    default_value: str
    description: str
    is_secret: bool


def write_configuration_documentation[T](
    config: type[T] | T,
    env_prefix: str | None = None,
    output_dir: Path = Path("docs/config"),
):
    """Creates both yaml example and markdown docs for configuration"""
    write_config_yaml_example(config, output_dir=output_dir)
    write_config_markdown(config, env_prefix, output_dir=output_dir)


def write_config_yaml_example[T](
    config: type[T] | T, output_dir: Path = Path("docs/config")
) -> None:
    """Creates [output_dir]/config.example.yaml with documented configuration entries."""
    if isinstance(config, type):
        cfg = config()
    else:
        cfg = config

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "config.example.yaml"

    lines = []

    def visit(field_name: str, field_type: str, entry: AppConfigEntry) -> None:
        default_value = getattr(cfg, field_name)

        if entry.is_secret:
            default_value = f"Masked[len:{len(str(default_value))}]"

        description = entry.description
        if len(description.strip()) == 0:
            description = field_name

        lines.append(_yaml_comment(f"{description}"))
        lines.append(_yaml_comment(f"Type: {field_type}"))
        lines.append(_yaml_comment(f"Is Secret: {entry.is_secret}"))
        lines.append(_yaml_line(key=field_name, val=default_value))
        lines.append("")

    visit_config_entries(cfg, visit)

    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_config_markdown[T](
    config: type[T] | T,
    env_prefix: str | None = None,
    output_dir: Path = Path("docs/config"),
) -> None:
    """Creates [output_dir]/DefaultConfiguration.md with configuration documentation and examples."""
    if isinstance(config, type):
        cfg = config()
    else:
        cfg = config

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "DefaultConfiguration.md"

    entries: list[MarkdownInfoEntry] = []

    def collect_entry(field_name: str, field_type: str, entry: AppConfigEntry) -> None:
        description = entry.description
        if len(description.strip()) == 0:
            description = field_name

        default_value = getattr(cfg, field_name)
        if entry.is_secret:
            default_value = f"Masked[len:{len(str(default_value))}]"

        entries.append(
            MarkdownInfoEntry(
                env_name=get_env_name(field_name, env_prefix),
                field_name=field_name,
                field_type=field_type,
                default_value=default_value,
                description=description,
                is_secret=entry.is_secret,
            )
        )

    visit_config_entries(cfg, collect_entry)

    lines = [
        "# Application Configuration",
        "",
        "## Configuration",
        "",
        "| ENV | Variable | Type | Default | Is Secret | Description |",
        "|---|---|---|---|---|---|",
    ]

    for info_entry in entries:
        lines.append(
            "| "
            f"{_markdown_table_cell(info_entry.env_name)} | "
            f"{_markdown_table_cell(info_entry.field_name)} | "
            f"{_markdown_table_cell(info_entry.field_type)} | "
            f"{_markdown_table_cell(info_entry.default_value)} | "
            f"{_markdown_table_cell(info_entry.is_secret)} | "
            f"{_markdown_table_cell(info_entry.description)} |"
        )

    lines.extend(
        [
            "",
            "## Docker Compose",
            "",
            "Example environment block using the default values:",
            "",
            "```yaml",
            "environment:",
        ]
    )

    for info_entry in entries:
        lines.append(
            f"  {_yaml_line(key=info_entry.env_name, val=_escape_value(info_entry.default_value))}"
        )

    lines.extend(
        [
            "```",
            "",
            "## Docker Run",
            "",
            "Example `docker run` command using the default values:",
            "",
            "```bash",
            "docker run \\",
        ]
    )

    for info_entry in entries:
        lines.append(
            f"  -e {info_entry.env_name}={shlex.quote(str(_escape_value(info_entry.default_value)))} \\"
        )

    lines.append("  your-image:latest")
    lines.append("```")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def _markdown_table_cell(value: object) -> str:
    value = _escape_value(value)
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("|", "&#124;")
    )


def _yaml_comment(input: object) -> str:
    text = str(input)
    result = "\n".join(f"# {line}" for line in text.splitlines()) or "#"
    return result


def _yaml_line(key: str, val: object) -> str:
    dumped = yaml.safe_dump(
        {key: val},
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        line_break="",
    ).rstrip()

    return dumped


def _escape_value(input: object) -> object:
    if isinstance(input, str):
        input = input.replace("```", "\\`\\`\\`")
        input = input.replace("\r\n", "\\r\\n")
        input = input.replace("\r", "\\r")
        input = input.replace("\n", "\\n")

    return input
