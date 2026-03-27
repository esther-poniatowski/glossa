"""Shared option validators for rule option_schema declarations."""

from __future__ import annotations

from glossa.errors import ConfigurationError


def validate_bool(value: object, key: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ConfigurationError(f"Option '{key}' must be a boolean.")


def validate_positive_int(value: object, key: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigurationError(f"Option '{key}' must be an integer.")
    if value < 1:
        raise ConfigurationError(f"Option '{key}' must be >= 1.")
    return value


def validate_string_tuple(value: object, key: str) -> tuple[str, ...]:
    if isinstance(value, str):
        raise ConfigurationError(
            f"Option '{key}' must be a sequence of strings, not a bare string."
        )
    if not isinstance(value, (list, tuple)):
        raise ConfigurationError(f"Option '{key}' must be a sequence of strings.")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ConfigurationError(f"Option '{key}' items must all be strings.")
        result.append(item)
    return tuple(result)
