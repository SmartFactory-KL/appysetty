from appysetty import AppConfigSource, read_configuration

from .define_config import ExampleConfig


def run():
    cfg = read_configuration(ExampleConfig, [AppConfigSource.ENV])

    print(cfg.port)
    print(cfg.api_key)


if __name__ == "__main__":
    run()
