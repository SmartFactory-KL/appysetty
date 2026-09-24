# Application Configuration

## Configuration

| ENV | Variable | Type | Default | Is Secret | Description |
|---|---|---|---|---|---|
| EXAMPLE_APP_HOST | host | str | localhost | False | Host to run the application on |
| EXAMPLE_APP_PORT | port | int | 8080 | False | port |
| EXAMPLE_APP_DEBUG | debug | bool | False | False | debug |
| EXAMPLE_APP_TIMEOUT | timeout | float | 5.0 | False | Request timeout in seconds |
| EXAMPLE_APP_WORKERS | workers | int | 4 | False | workers |
| EXAMPLE_APP_API_KEY | api_key | str | Masked[len:0] | True | API key used to access external services |

## Docker Compose

Example environment block using the default values:

```yaml
environment:
  EXAMPLE_APP_HOST: localhost
  EXAMPLE_APP_PORT: 8080
  EXAMPLE_APP_DEBUG: False
  EXAMPLE_APP_TIMEOUT: 5.0
  EXAMPLE_APP_WORKERS: 4
  EXAMPLE_APP_API_KEY: Masked[len:0]
```

## Docker Run

Example `docker run` command using the default values:

```bash
docker run \
  -e EXAMPLE_APP_HOST=localhost \
  -e EXAMPLE_APP_PORT=8080 \
  -e EXAMPLE_APP_DEBUG=False \
  -e EXAMPLE_APP_TIMEOUT=5.0 \
  -e EXAMPLE_APP_WORKERS=4 \
  -e EXAMPLE_APP_API_KEY='Masked[len:0]'
  your-image:latest
```
