# ApPySetty

A simple configuration helper using a single dataclass to read configuration and create documentation from, inspired by [AppGofig](https://github.com/smartfactory-kl/appgofig).

# Install

[TODO]

# Usage

## Define Config

First you need to define a dataclass which contains all the configuration options you want to support.

```python
@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    timeout: float = 5.0
```

> [!note]
> As of now, only `str`, `int`, `float` and `bool` are supported. Experience shows that other types are usually better handled on the user side

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
```

Both variants can be mixed. If no description is provided, the name of the field will be the description.

## Read Config

To read the config, use:

```python
cfg = read_configuration(ConfigWithMetadata, AppConfigSource.ENV)
```

After that `cfg` should have all configurations with auto-complete ready for you.

You can also pass an instance and use multiple sources, where each source will overwrite the previous one:

```python
cfg = read_configuration(ConfigWithMetadata(), [AppConfigSource.ENV, AppConfigSource.YAML])
```

The available sources are:

| Key                    | Source      | Description                                                                              |
| ---------------------- | ----------- | ---------------------------------------------------------------------------------------- |
| `AppConfigSource.ENV`  | Environment | This will read config from environment, using UPPER_SNAKE_CASE variant of the field name |
| `AppConfigSource.YAML` | YAML file   | This will read the config from a yaml file, only matching field name exactly             |
| `AppConfigSource.TOML` | TOML file   | TBD                                                                                      |

#### Options

Options can be used to customize the config:

```python
cfg = read_configuration(ConfigWithMetadata, [AppConfigSource.ENV, AppConfigSource.YAML], AppConfigOptions(
    env_prefix="MY_APP_PREFIX",
    yaml_path="config.dev.yaml",
    overwrite={"port": "8000"}
))
```

| Option       | Description                                                                                               |
| ------------ | --------------------------------------------------------------------------------------------------------- |
| `env_prefix` | A Prefix that will be prepended to all field names using UPPER_SNAKE_CASE to read environment .           |
| `yaml_path`  | Setting a specific yaml file to use. It unset, the tool will look for `(config)/config.y(a)ml`.           |
| `overwrite`  | This accepts a mapping. values set with overwrite will always overwrite anything else. Mainly for testing |

## Write Documentation

The second feature of this tool is automated creation of a few documentation items for configuration options:

- `config.example.yaml` containing an example yaml file with default values and descriptive comments (if descriptions were defined)
- `DefaultConfiguration.md` containing a table of all options with ENV variant, a docker environment block for docker compose and a docker run example command with all -e set.

To create the documentation, use:

```python
# Create both documents
write_config_documentation(
    ConfigWithMetadata,
    env_prefix="MY_APP_PREFIX",
    output_dir=Path()
)

# Only create yaml example
write_config_yaml_example(
    ConfigWithMetadata,
    output_dir=Path()
)

# Only create markdown document
write_config_markdown(
    ConfigWithMetadata,
    env_prefix="MY_APP_PREFIX",
    output_dir=Path()
)
```

> [!note]
> `env_prefix` defaults to "" if not set and `output_dir` defaults to `./docs/config` if not set.

# Examples

This repo contains a few examples within `/examples`. To run them, use:

```bash
uv run python -m example.write_documentation
uv run python -m example.read_documentation
```

# Development

## Running tests

Test command:

```bash
uv run pytest --cov=appysetty --cov-report=term-missing
```
