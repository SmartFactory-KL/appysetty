def get_env_name(field_name: str, prefix: str | None) -> str:
    """Returns MY_PREFIX_FIELD_NAME from MY_PREFIX(_) and the fields name"""
    name = field_name.upper()

    if prefix is None or len(prefix.strip()) == 0:
        return name

    return f"{prefix.rstrip('_')}_{name}"
