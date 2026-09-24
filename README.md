[![Tests](https://github.com/SmartFactory-KL/appysetty/actions/workflows/test.yml/badge.svg)](https://github.com/SmartFactory-KL/appysetty/actions/workflows/test.yml)
[![PyPI version](https://img.shields.io/pypi/v/appysetty.svg)](https://pypi.org/project/appysetty/)

# ApPySetty ⚙️

**A simple, type-safe Python library for managing application configuration from Environment variables and YAML.**

ApPySetty uses Python dataclasses as the single definition of your application configuration. It can load values from configuration files and environment variables and generate documentation from the same definition.

## Quick Start

Install:

```bash
uv add appysetty
```

Define your configuration and read from Environment:

```python
from dataclasses import dataclass

from appysetty import EnvSource, read_configuration


@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    debug: bool = False


config = read_configuration(
    Config,
    EnvSource(),
)
```

Or load values from YAML:

```yaml
host: localhost
port: 8080
debug: false
```

```python
config = read_configuration(
    Config,
    YamlSource(path="yaml_file.yaml"),
)
```

Or both:

```python
config = read_configuration(
    Config,
    [YamlSource(path="yaml_file.yaml"), EnvSource()],
)
```

> [!note]
> Sources are applied in order. Later sources override values from earlier sources.

And also document your configuration with an example .yaml and a markdown document:

```python
write_configuration_documentation(Config, output_dir=Path("./docs"))
```

> [!caution]
> Please note that `.strip()` is applied to all string values which removes leading and trailing whitespaces. Inputs like `   hello  ` would become `hello`.

## Configuration Sources

ApPySetty uses `AppConfigSource` as the interface to define loaders. These sources are loaded and applied in the order they are provided.

```python
cfg = read_configuration(
    Config, [YamlSource(...), TomlSource(...), EnvSource(...), DictSource(...)]
)
```

In the example above, YAML values are applied first, then environment variables, and finally dictionary values. Later sources override values from earlier sources.

The available sources are:

#### `EnvSource()` - Reading from Environment

```python
cfg = read_configuration(Config, EnvSource(prefix="MY_PREFIX"))
```

For every key within the config, the key is converted to UPPER_SNAKE_CASE, the optional prefix is applied and the resulting key is used to read a value from the environment.

> [!note]
> The prefix itself will not be converted to UPPER_SNAKE_CASE

#### `DictSource()` - Reading from a Dict

```python
cfg = read_configuration(Config, DictSource(input={"key": "val"}))
```

Values are read from the provided dictionary using the configuration field names as keys. Unknown dictionary keys are rejected.

#### `YamlSource()` - Reading from a .yaml file

```python
cfg = read_configuration(Config, YamlSource(path="", required=True))
```

If path is specified, that file is used. Otherwise, the first existing file from the following list is used:

```text
config.yml
config.yaml
config/config.yml
config/config.yaml
```

If required is False, a missing file will simply be ignored. If required is True an AppConfigError is raised. By default required is set to True.

> [!note]
> Only flat mappings are allowed and the YAML key must match the config key exactly

#### `TomlSource()` - Reading from a .toml file

```python
cfg = read_configuration(Config, TomlSource(path="", required=True))
```

If path is specified, that file is used. Otherwise, the first existing file from the following list is used:

```text
config.toml
config/config.toml
```

If required is False, a missing file will simply be ignored. If required is True an AppConfigError is raised. By default required is set to True.

> [!note]
> Only flat mappings are allowed and the TOML key must match the config key exactly

#### Define your own source

All sources are based on the `AppConfigSource`. To extend the list of sources, you could supply your own implementation:

```python
@dataclass(frozen=True)
class MyOwnSource(AppConfigSource):
    """Example for your source, based on the DictSource"""

    input: dict[str, str]

    def load(self, config_type_hints):
        values: dict[str, object] = {}

        for name, value in self.input.items():
            ...

        return values
```

## Define Config

The simplest form of a config class looks like this:

```python
@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    timeout: float = 5.0
```

> [!note]
> As of now, only `str`, `int`, `float` and `bool` are supported

You can also extend your dataclass with additional information for better documentation and for masking secrets:

```python
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

    debug: bool = False
```

Both variants can be mixed. If no description is provided, the name of the field will be the description.

### Write Documentation

One feature of this tool is automating the documentation items for configuration options:

- `config.example.yaml` containing an example YAML file with default values and descriptive comments (if descriptions were defined)
- `DefaultConfiguration.md` containing a table of all options with ENV variant, a docker compose `environment` block for docker compose and a docker run example command with all -e set.

To create the documentation, use:

```python
# Create both documents
write_configuration_documentation(
    ConfigWithMetadata, env_prefix="MY_APP_PREFIX", output_dir=Path()
)

# Only create YAML example
write_config_yaml_example(ConfigWithMetadata, output_dir=Path())

# Only create markdown document
write_config_markdown(ConfigWithMetadata, env_prefix="MY_APP_PREFIX", output_dir=Path())
```

> [!note]
> `env_prefix` defaults to "" if not set and `output_dir` defaults to `./docs/config` if not set.

> [!caution]
> Make sure to always match the `env_prefix` to the actual prefix used for the EnvSource if applied

## Development

Clone the repository and install the development dependencies:

```bash
git clone https://github.com/SmartFactory-KL/appysetty.git
cd appysetty
uv sync
```

Run the tests:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov=appysetty --cov-report=term-missing
```

Run the examples:

```bash
uv run python -m examples.write_documentation
uv run python -m examples.read_documentation
```

Run Ruff:

```bash
uv run ruff check
uv run ruff format .
```

## License

ApPySetty is licensed under the [MIT License](LICENSE).
