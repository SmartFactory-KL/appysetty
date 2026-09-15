from pathlib import Path

from appysetty import write_configuration_documentation

from .define_config import ExampleConfig


def run():
    write_configuration_documentation(
        ExampleConfig,
        env_prefix="EXAMPLE_APP",
        output_dir=Path("./examples/example_output"),
    )


if __name__ == "__main__":
    run()
