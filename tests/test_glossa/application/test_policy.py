"""Tests for glossa.application.policy."""

from __future__ import annotations

import pytest

from glossa.application.configuration import (
    FixApplyMode,
    FixPolicy,
    GlossaConfig,
    OutputFormat,
    OutputOptions,
    RuleSelection,
    SuppressionPolicy,
)
from glossa.core.contracts import Severity
from glossa.application.policy import (
    is_rule_suppressed,
    matches_pattern,
    parse_inline_suppression,
    resolve_rule_policy,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def base_config() -> GlossaConfig:
    """A GlossaConfig with sensible defaults for testing."""
    return GlossaConfig(
        rules=RuleSelection(
            select=("D1xx", "D2xx"),
            ignore=(),
            severity_overrides={},
            per_file_ignores={},
            rule_options={},
        ),
        suppressions=SuppressionPolicy(
            inline_enabled=True,
            directive_prefix="glossa: ignore=",
        ),
        fix=FixPolicy(
            enabled=False,
            apply=FixApplyMode.NEVER,
            validate_after_apply=False,
        ),
        output=OutputOptions(
            format=OutputFormat.TEXT,
            color=False,
            show_source=True,
        ),
    )


# ---------------------------------------------------------------------------
# matches_pattern
# ---------------------------------------------------------------------------


def test_matches_pattern_exact() -> None:
    """An exact pattern matches only the identical rule code."""
    assert matches_pattern("D100", "D100") is True


def test_matches_pattern_wildcard() -> None:
    """A pattern ending in 'x' characters matches any rule with the same prefix."""
    assert matches_pattern("D100", "D1xx") is True
    assert matches_pattern("D111", "D1xx") is True


def test_matches_pattern_no_match() -> None:
    """A wildcard pattern does not match a rule with a different prefix."""
    assert matches_pattern("D100", "D2xx") is False


# ---------------------------------------------------------------------------
# parse_inline_suppression
# ---------------------------------------------------------------------------


def test_parse_inline_suppression() -> None:
    """A line with a glossa: ignore= directive returns a tuple of rule codes."""
    line = "def foo():  # glossa: ignore=D200,D205"
    result = parse_inline_suppression(line)
    assert result == ("D200", "D205")


def test_parse_inline_suppression_none() -> None:
    """A line without a suppression directive returns None."""
    line = "def foo():  # some unrelated comment"
    assert parse_inline_suppression(line) is None


# ---------------------------------------------------------------------------
# is_rule_suppressed
# ---------------------------------------------------------------------------


def test_is_rule_suppressed() -> None:
    """Returns True when the rule code is present in the suppressions tuple."""
    assert is_rule_suppressed("D200", ("D200", "D205")) is True
    assert is_rule_suppressed("D300", ("D200", "D205")) is False


# ---------------------------------------------------------------------------
# resolve_rule_policy
# ---------------------------------------------------------------------------


def test_resolve_rule_policy_enabled(base_config: GlossaConfig) -> None:
    """A rule matching a pattern in the select list is enabled."""
    policy = resolve_rule_policy("D100", "src/foo.py", base_config)
    assert policy.enabled is True


def test_resolve_rule_policy_ignored(base_config: GlossaConfig) -> None:
    """A rule present in the ignore list is disabled, even if also in select."""
    config = GlossaConfig(
        rules=RuleSelection(
            select=("D1xx",),
            ignore=("D100",),
            severity_overrides={},
            per_file_ignores={},
            rule_options={},
        ),
        suppressions=base_config.suppressions,
        fix=base_config.fix,
        output=base_config.output,
    )
    policy = resolve_rule_policy("D100", "src/foo.py", config)
    assert policy.enabled is False


def test_resolve_rule_policy_per_file(base_config: GlossaConfig) -> None:
    """per_file_ignores disables a rule for files matching the glob pattern."""
    config = GlossaConfig(
        rules=RuleSelection(
            select=("D1xx",),
            ignore=(),
            severity_overrides={},
            per_file_ignores={"src/legacy/*.py": ("D100",)},
            rule_options={},
        ),
        suppressions=base_config.suppressions,
        fix=base_config.fix,
        output=base_config.output,
    )
    # Matching file: rule should be disabled
    policy_matching = resolve_rule_policy("D100", "src/legacy/old.py", config)
    assert policy_matching.enabled is False

    # Non-matching file: rule should remain enabled
    policy_other = resolve_rule_policy("D100", "src/new/fresh.py", config)
    assert policy_other.enabled is True
