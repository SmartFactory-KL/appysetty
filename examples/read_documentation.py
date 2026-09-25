from appysetty import EnvSource, read_configuration

from .define_config import ExampleConfig


def run():
    cfg = read_configuration(ExampleConfig, EnvSource())

    print(cfg.port)
    print(cfg.timeout)
    print(cfg.workers)
    print(cfg.api_key)


if __name__ == "__main__":
    run()
