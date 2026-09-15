from dataclasses import dataclass
from typing import Annotated

from appysetty.model import AppConfigEntry


@dataclass
class ExampleConfig:
    host: Annotated[
        str,
        AppConfigEntry(
            description="Host to run the application on",
            is_secret=False,
        ),
    ] = "localhost"

    # You can also only annotate what actually needs a description - unlike this port
    port: int = 8080

    debug: bool = False

    timeout: Annotated[
        float,
        AppConfigEntry(
            description="Request timeout in seconds",
            is_secret=False,
        ),
    ] = 5.0

    workers: int = 4

    api_key: Annotated[
        str,
        AppConfigEntry(
            description="API key used to access external services",
            is_secret=True,
        ),
    ] = ""
