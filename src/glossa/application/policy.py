"""Rule selection, per-file overrides, and inline suppressions."""

from __future__ import annotations

import fnmatch
from types import MappingProxyType
from typing import TYPE_CHECKING, Mapping

from glossa.application.configuration import GlossaConfig, RuleSelection
from glossa.domain.contracts import RulePolicy, Severity

if TYPE_CHECKING:
    from glossa.domain.rules import RuleMetadata


# ---------------------------------------------------------------------------
# Pattern Helpers
# ---------------------------------------------------------------------------


def matches_rule(rule_metadata: RuleMetadata, pattern: str) -> bool:
    """Return True if *pattern* matches the rule's name or group."""
    return rule_metadata.name == pattern or rule_metadata.group == pattern


def matches_file_pattern(source_id: str, glob_pattern: str) -> bool:
    """Return True if source_id matches glob_pattern using fnmatch."""
    return fnmatch.fnmatch(source_id, glob_pattern)


# ---------------------------------------------------------------------------
# Policy Resolution
# ---------------------------------------------------------------------------


def resolve_rule_policy(
    rule_metadata: RuleMetadata,
    source_id: str,
    config: GlossaConfig,
) -> RulePolicy:
    """Resolve whether a rule is enabled for a given source file.

    Resolution order
    ----------------
    1. A rule in ``config.rules.ignore`` is always disabled.
    2. A rule matching any pattern in ``config.rules.select`` is enabled.
    3. ``config.rules.per_file_ignores``: if source_id matches a glob pattern
       whose rule list includes the rule name or group, the rule is disabled.
    4. Severity is taken from ``config.rules.severity_overrides`` when present,
       otherwise from the rule's ``default_severity``.
    5. Options are merged from the rule's ``option_schema`` defaults with any
       user-supplied overrides in ``config.rules.rule_options``.
    """
    rule_name = rule_metadata.name
    rules = config.rules
    options = _resolve_options(rule_metadata, rules)

    for ignored in rules.ignore:
        if matches_rule(rule_metadata, ignored):
            return RulePolicy(
                enabled=False,
                severity=_resolve_severity(rule_name, rules.severity_overrides, rule_metadata.default_severity),
                options=options,
            )

    selected = any(matches_rule(rule_metadata, pattern) for pattern in rules.select)

    per_file_disabled = False
    for glob_pattern, ignored_rules in rules.per_file_ignores.items():
        if matches_file_pattern(source_id, glob_pattern):
            if any(matches_rule(rule_metadata, r) for r in ignored_rules):
                per_file_disabled = True
                break

    enabled = selected and not per_file_disabled
    severity = _resolve_severity(rule_name, rules.severity_overrides, rule_metadata.default_severity)

    return RulePolicy(enabled=enabled, severity=severity, options=options)


def _resolve_severity(
    rule_name: str,
    severity_overrides: Mapping[str, Severity],
    default_severity: Severity,
) -> Severity:
    return severity_overrides.get(rule_name, default_severity)


def _resolve_options(
    rule_metadata: RuleMetadata,
    rules: RuleSelection,
) -> Mapping[str, object]:
    """Merge rule schema defaults with user-supplied options, coercing via validators."""
    result: dict[str, object] = {d.key: d.default for d in rule_metadata.option_schema}
    schema_map = {d.key: d for d in rule_metadata.option_schema}
    user = rules.rule_options.get(rule_metadata.name, {})
    for key, value in user.items():
        descriptor = schema_map.get(key)
        result[key] = descriptor.validator(value, key) if descriptor is not None else value
    return MappingProxyType(result)


# ---------------------------------------------------------------------------
# Inline Suppressions
# ---------------------------------------------------------------------------


def parse_inline_suppression(
    line: str,
    directive_prefix: str = "glossa: ignore=",
) -> tuple[str, ...] | None:
    """Parse an inline suppression comment from a source line.

    Examples
    --------
    >>> parse_inline_suppression('x = 1  # glossa: ignore=missing-period,first-person-voice')
    ('missing-period', 'first-person-voice')
    >>> parse_inline_suppression('x = 1  # some other comment') is None
    True
    """
    comment_start = line.find("#")
    if comment_start == -1:
        return None

    comment_body = line[comment_start + 1:].strip()

    if not comment_body.startswith(directive_prefix):
        return None

    names_str = comment_body[len(directive_prefix):]
    names = tuple(name.strip() for name in names_str.split(",") if name.strip())

    return names if names else None


def is_rule_suppressed(rule_name: str, suppressions: tuple[str, ...]) -> bool:
    """Return True if rule_name is present in the suppressions tuple."""
    return rule_name in suppressions
