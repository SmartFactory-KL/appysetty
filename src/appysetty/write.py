import shlex
from dataclasses import dataclass
from pathlib import Path

from appysetty.env import get_env_name
from appysetty.model import AppConfigEntry
from appysetty.read import visit_config_entries

_CONFIG_DOCS_PATH = Path("docs/config")


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

        description = entry.description
        if len(description.strip()) == 0:
            description = field_name

        lines.append(f"# {description}")
        lines.append(f"# Type: {field_type}")
        lines.append(f"# Is Secret: {entry.is_secret}")
        lines.append(f"{field_name}: {_encase_str_in_quotes(default_value)}")
        lines.append(" ")

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

        entries.append(
            MarkdownInfoEntry(
                env_name=get_env_name(env_prefix, field_name),
                field_name=field_name,
                field_type=field_type,
                default_value=getattr(cfg, field_name),
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
            f"{info_entry.env_name} | "
            f"{info_entry.field_name} | "
            f"`{info_entry.field_type}` | "
            f"`{info_entry.default_value}` | "
            f"{info_entry.is_secret} | "
            f"{info_entry.description} |"
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
        lines.append(f"  {info_entry.env_name}: {info_entry.default_value}")

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

    docker_envs = []
    for info_entry in entries:
        docker_envs.append(
            f"-e {info_entry.env_name}={shlex.quote(str(info_entry.default_value))}"
        )

    for index, env in enumerate(docker_envs):
        suffix = " \\" if index < len(docker_envs) - 1 else ""
        lines.append(f"  {env}{suffix}")

    lines.append("  your-image:latest")
    lines.append("```")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def _encase_str_in_quotes(value: object) -> str:
    """Creates "value" from value for a str, otherwise return str(value)"""
    if isinstance(value, str):
        return f'"{value!s}"'

    return f"{value!s}"
