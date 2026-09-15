from pathlib import Path

from appysetty.write import write_config_documentation

from .define_config import ExampleConfig


def run():
    write_config_documentation(
        ExampleConfig,
        env_prefix="EXAMPLE_APP",
        output_dir=Path("./examples/example_output"),
    )


if __name__ == "__main__":
    run()
