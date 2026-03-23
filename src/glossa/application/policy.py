"""Rule selection, per-file overrides, and inline suppressions."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from typing import Mapping

from glossa.application.contracts import GlossaConfig, Severity


# ---------------------------------------------------------------------------
# Resolved Policy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResolvedRulePolicy:
    enabled: bool
    severity: Severity
    options: Mapping[str, object]


# ---------------------------------------------------------------------------
# Pattern Helpers
# ---------------------------------------------------------------------------


def matches_pattern(rule_code: str, pattern: str) -> bool:
    """Return True if rule_code matches pattern.

    An exact match always succeeds. A pattern ending with one or more ``x``
    characters (case-insensitive) acts as a prefix wildcard: the non-``x``
    prefix of the pattern must match the same-length prefix of rule_code.

    Examples
    --------
    >>> matches_pattern("D100", "D1xx")
    True
    >>> matches_pattern("D200", "D1xx")
    False
    >>> matches_pattern("D102", "D102")
    True
    >>> matches_pattern("D102", "D103")
    False
    """
    if rule_code == pattern:
        return True

    # Strip trailing x/X characters to find the fixed prefix.
    stripped = pattern.rstrip("xX")
    if stripped == pattern:
        # No wildcards present and not an exact match.
        return False

    # The number of wildcard positions equals the number of stripped chars.
    wildcard_count = len(pattern) - len(stripped)
    prefix_len = len(stripped)

    if len(rule_code) != len(stripped) + wildcard_count:
        return False

    return rule_code[:prefix_len].upper() == stripped.upper()


def matches_file_pattern(source_id: str, glob_pattern: str) -> bool:
    """Return True if source_id matches glob_pattern using fnmatch."""
    return fnmatch.fnmatch(source_id, glob_pattern)


# ---------------------------------------------------------------------------
# Policy Resolution
# ---------------------------------------------------------------------------


def resolve_rule_policy(
    rule_code: str,
    source_id: str,
    config: GlossaConfig,
    default_severity: Severity = Severity.WARNING,
) -> ResolvedRulePolicy:
    """Resolve whether a rule is enabled for a given source file.

    Resolution order
    ----------------
    1. A rule in ``config.rules.ignore`` is always disabled.
    2. A rule matching any pattern in ``config.rules.select`` is enabled.
    3. ``config.rules.per_file_ignores``: if source_id matches a glob pattern
       whose rule list includes rule_code, the rule is disabled.
    4. Severity is taken from ``config.rules.severity_overrides`` when present,
       otherwise from *default_severity*.
    5. Options are taken from ``config.rules.rule_options`` when present,
       otherwise an empty mapping is used.

    Parameters
    ----------
    rule_code:
        The rule identifier to resolve (e.g. ``"D100"``).
    source_id:
        The path or identifier of the source file being linted.
    config:
        The active glossa configuration.
    default_severity:
        Severity to use when no override is configured for the rule.

    Returns
    -------
    ResolvedRulePolicy
        The fully-resolved policy for the rule/file combination.
    """
    rules = config.rules

    # Step 1: ignore list disables the rule unconditionally.
    for ignored in rules.ignore:
        if matches_pattern(rule_code, ignored):
            return ResolvedRulePolicy(
                enabled=False,
                severity=_resolve_severity(rule_code, rules.severity_overrides, default_severity),
                options=rules.rule_options.get(rule_code, {}),
            )

    # Step 2: select list enables the rule if any pattern matches.
    selected = any(matches_pattern(rule_code, pattern) for pattern in rules.select)

    # Step 3: per-file ignores can still disable even a selected rule.
    per_file_disabled = False
    for glob_pattern, ignored_codes in rules.per_file_ignores.items():
        if matches_file_pattern(source_id, glob_pattern):
            if rule_code in ignored_codes:
                per_file_disabled = True
                break

    enabled = selected and not per_file_disabled

    # Steps 4 & 5: severity and options.
    severity = _resolve_severity(rule_code, rules.severity_overrides, default_severity)
    options: Mapping[str, object] = rules.rule_options.get(rule_code, {})

    return ResolvedRulePolicy(enabled=enabled, severity=severity, options=options)


def _resolve_severity(
    rule_code: str,
    severity_overrides: Mapping[str, Severity],
    default_severity: Severity,
) -> Severity:
    """Return the effective severity for a rule code."""
    return severity_overrides.get(rule_code, default_severity)


# ---------------------------------------------------------------------------
# Inline Suppressions
# ---------------------------------------------------------------------------


def parse_inline_suppression(
    line: str,
    directive_prefix: str = "glossa: ignore=",
) -> tuple[str, ...] | None:
    """Parse an inline suppression comment from a source line.

    Looks for a comment of the form ``# <directive_prefix><codes>`` where
    *codes* is a comma-separated list of rule codes.

    Parameters
    ----------
    line:
        A single source line, possibly containing an inline comment.
    directive_prefix:
        The prefix that identifies a suppression directive inside a comment.
        Defaults to ``"glossa: ignore="``.

    Returns
    -------
    tuple[str, ...] | None
        A tuple of suppressed rule codes, or ``None`` if the line contains no
        matching suppression directive.

    Examples
    --------
    >>> parse_inline_suppression('x = 1  # glossa: ignore=D100,D101')
    ('D100', 'D101')
    >>> parse_inline_suppression('x = 1  # some other comment') is None
    True
    """
    # Find the first '#' that starts a comment.
    comment_start = line.find("#")
    if comment_start == -1:
        return None

    comment_body = line[comment_start + 1 :].strip()

    if not comment_body.startswith(directive_prefix):
        return None

    codes_str = comment_body[len(directive_prefix):]
    codes = tuple(code.strip() for code in codes_str.split(",") if code.strip())

    return codes if codes else None


def is_rule_suppressed(rule_code: str, suppressions: tuple[str, ...]) -> bool:
    """Return True if rule_code is present in the suppressions tuple.

    Parameters
    ----------
    rule_code:
        The rule identifier to check (e.g. ``"D100"``).
    suppressions:
        A tuple of rule codes obtained from :func:`parse_inline_suppression`.
    """
    return rule_code in suppressions
