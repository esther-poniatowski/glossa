"""Typed configuration models and validation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Sequence

from glossa.core.contracts import Severity
from glossa.errors import ConfigurationError

DEFAULT_RULE_SELECT = ("D1xx", "D2xx", "D3xx", "D4xx", "D5xx")
DEFAULT_TRIVIAL_DUNDER_ALLOWLIST = (
    "__init__",
    "__new__",
    "__del__",
    "__repr__",
    "__str__",
)

@dataclass(frozen=True)
class RuleOptionDescriptor:
    key: str
    default: object
    validator: object  # Callable[[object, str], object]


# Single source of truth for built-in rule options: key, default, validator.
_RULE_OPTION_SCHEMA: dict[str, tuple[RuleOptionDescriptor, ...]] = {
    "D102": (
        RuleOptionDescriptor("include_test_functions", False, lambda v, p: _bool(v, p)),
        RuleOptionDescriptor("include_private_helpers", False, lambda v, p: _bool(v, p)),
    ),
    "D104": (
        RuleOptionDescriptor("simple_property_requires_returns", True, lambda v, p: _bool(v, p)),
    ),
    "D108": (
        RuleOptionDescriptor("inventory_threshold", 2, lambda v, p: _positive_int(v, p)),
    ),
    "D306": (
        RuleOptionDescriptor("api_entry_modules", (), lambda v, p: _string_tuple(v, p)),
    ),
    "D501": (
        RuleOptionDescriptor("trivial_dunder_allowlist", DEFAULT_TRIVIAL_DUNDER_ALLOWLIST, lambda v, p: _string_tuple(v, p)),
    ),
}


def _rule_option_defaults(rule_code: str) -> dict[str, object]:
    """Derive defaults from the schema for a given rule code."""
    descriptors = _RULE_OPTION_SCHEMA.get(rule_code, ())
    return {d.key: d.default for d in descriptors}

class OutputFormat(Enum):
    TEXT = "text"
    JSON = "json"


class FixApplyMode(Enum):
    NEVER = "never"
    SAFE = "safe"
    UNSAFE = "unsafe"


@dataclass(frozen=True)
class RuleSelection:
    select: tuple[str, ...]
    ignore: tuple[str, ...]
    severity_overrides: Mapping[str, Severity]
    per_file_ignores: Mapping[str, tuple[str, ...]]
    rule_options: Mapping[str, Mapping[str, object]]


@dataclass(frozen=True)
class SuppressionPolicy:
    inline_enabled: bool
    directive_prefix: str


@dataclass(frozen=True)
class FixPolicy:
    enabled: bool
    apply: FixApplyMode
    validate_after_apply: bool


@dataclass(frozen=True)
class OutputOptions:
    format: OutputFormat
    color: bool
    show_source: bool


@dataclass(frozen=True)
class GlossaConfig:
    rules: RuleSelection
    suppressions: SuppressionPolicy
    fix: FixPolicy
    output: OutputOptions


def resolve_config(raw: Mapping[str, object]) -> GlossaConfig:
    """Validate a raw config mapping and return typed configuration."""
    rules_raw = _mapping(raw.get("rules", {}), "rules")
    suppressions_raw = _mapping(raw.get("suppressions", {}), "suppressions")
    fix_raw = _mapping(raw.get("fix", {}), "fix")
    output_raw = _mapping(raw.get("output", {}), "output")

    severity_overrides_raw = _mapping(
        rules_raw.get("severity_overrides", {}), "rules.severity_overrides"
    )
    per_file_ignores_raw = _mapping(
        rules_raw.get("per_file_ignores", {}), "rules.per_file_ignores"
    )
    rule_options_raw = _mapping(rules_raw.get("rule_options", {}), "rules.rule_options")

    rules = RuleSelection(
        select=_string_tuple(
            rules_raw.get("select", DEFAULT_RULE_SELECT),
            "rules.select",
        ),
        ignore=_string_tuple(rules_raw.get("ignore", ()), "rules.ignore"),
        severity_overrides=_freeze_mapping(
            {
                code: _enum_member(Severity, value, f"rules.severity_overrides.{code}")
                for code, value in severity_overrides_raw.items()
            }
        ),
        per_file_ignores=_freeze_mapping(
            {
                pattern: _string_tuple(codes, f"rules.per_file_ignores.{pattern}")
                for pattern, codes in per_file_ignores_raw.items()
            }
        ),
        rule_options=_freeze_mapping(
            {
                code: _freeze_mapping(
                    _resolve_rule_options(code, _mapping(value, f"rules.rule_options.{code}"))
                )
                for code, value in rule_options_raw.items()
            }
        ),
    )

    suppressions = SuppressionPolicy(
        inline_enabled=_bool(
            suppressions_raw.get("inline_enabled", True),
            "suppressions.inline_enabled",
        ),
        directive_prefix=_string(
            suppressions_raw.get("directive_prefix", "glossa: ignore="),
            "suppressions.directive_prefix",
        ),
    )

    fix = FixPolicy(
        enabled=_bool(fix_raw.get("enabled", True), "fix.enabled"),
        apply=_enum_member(FixApplyMode, fix_raw.get("apply", FixApplyMode.SAFE.value), "fix.apply"),
        validate_after_apply=_bool(
            fix_raw.get("validate_after_apply", True),
            "fix.validate_after_apply",
        ),
    )

    output = OutputOptions(
        format=_enum_member(
            OutputFormat,
            output_raw.get("format", OutputFormat.TEXT.value),
            "output.format",
        ),
        color=_bool(output_raw.get("color", True), "output.color"),
        show_source=_bool(output_raw.get("show_source", True), "output.show_source"),
    )

    return GlossaConfig(
        rules=rules,
        suppressions=suppressions,
        fix=fix,
        output=output,
    )


def config_with_overrides(
    config: GlossaConfig,
    *,
    select: Sequence[str] | None = None,
    ignore: Sequence[str] | None = None,
    output_format: OutputFormat | None = None,
    color: bool | None = None,
) -> GlossaConfig:
    """Return a copy of *config* with CLI-style overrides applied."""
    rules = config.rules
    output = config.output

    if select is not None or ignore is not None:
        rules = replace(
            rules,
            select=tuple(select) if select is not None else rules.select,
            ignore=tuple(ignore) if ignore is not None else rules.ignore,
        )

    if output_format is not None or color is not None:
        output = replace(
            output,
            format=output_format or output.format,
            color=color if color is not None else output.color,
        )

    if rules is config.rules and output is config.output:
        return config

    return replace(config, rules=rules, output=output)


def _resolve_rule_options(rule_code: str, raw: Mapping[str, object]) -> dict[str, object]:
    """Validate and merge user-supplied options for *rule_code*.

    Returns a plain dict with defaults applied for any keys the user did not
    set.  Unknown keys for built-in rules raise ``ConfigurationError``;
    unknown keys for plugin rules are passed through.
    """
    descriptors = _RULE_OPTION_SCHEMA.get(rule_code)
    is_builtin = descriptors is not None
    schema_map = {d.key: d for d in descriptors} if descriptors else {}
    result: dict[str, object] = _rule_option_defaults(rule_code)

    for key, value in raw.items():
        descriptor = schema_map.get(key)
        if descriptor is None:
            if is_builtin:
                raise ConfigurationError(
                    f"Unknown option {key!r} for built-in rule {rule_code!r}"
                )
            result[key] = value
            continue
        result[key] = descriptor.validator(value, key)  # type: ignore[operator]

    return result


def _mapping(value: object, path: str) -> Mapping[str, object]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return value
    raise ConfigurationError(f"{path} must be a mapping.")


def _string(value: object, path: str) -> str:
    if isinstance(value, str):
        return value
    raise ConfigurationError(f"{path} must be a string.")


def _bool(value: object, path: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ConfigurationError(f"{path} must be a boolean.")


def _positive_int(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigurationError(f"{path} must be an integer.")
    if value < 1:
        raise ConfigurationError(f"{path} must be greater than or equal to 1.")
    return value


def _string_tuple(value: object, path: str) -> tuple[str, ...]:
    if isinstance(value, str):
        raise ConfigurationError(f"{path} must be a sequence of strings, not a string.")
    if not isinstance(value, Sequence):
        raise ConfigurationError(f"{path} must be a sequence of strings.")
    strings: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ConfigurationError(f"{path} must contain only strings.")
        strings.append(item)
    return tuple(strings)


def _enum_member(enum_cls: type[Enum], value: object, path: str) -> Enum:
    if not isinstance(value, str):
        raise ConfigurationError(f"{path} must be a string.")
    try:
        return enum_cls(value)
    except ValueError as exc:
        choices = ", ".join(member.value for member in enum_cls)
        raise ConfigurationError(f"{path} must be one of: {choices}.") from exc


def _freeze_mapping(values: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(values))
