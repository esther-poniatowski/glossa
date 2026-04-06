"""Tests for glossa.application.policy."""

from __future__ import annotations

import pytest

from glossa.application.configuration import (
    DEFAULT_SECTION_ORDER,
    FixApplyMode,
    FixPolicy,
    GlossaConfig,
    OutputFormat,
    OutputOptions,
    ParsingOptions,
    RuleSelection,
    SuppressionPolicy,
)
from glossa.domain.contracts import Severity
from glossa.application.policy import (
    is_rule_suppressed,
    matches_rule,
    parse_inline_suppression,
    resolve_rule_policy,
)
from glossa.domain.rules import RuleMetadata


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def base_config() -> GlossaConfig:
    """A GlossaConfig with sensible defaults for testing."""
    return GlossaConfig(
        rules=RuleSelection(
            select=("presence", "prose"),
            ignore=(),
            severity_overrides={},
            per_file_ignores={},
            rule_options={},
            section_order=DEFAULT_SECTION_ORDER,
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
        parsing=ParsingOptions(section_aliases={}),
    )


# ---------------------------------------------------------------------------
# matches_rule
# ---------------------------------------------------------------------------


def test_matches_rule_by_name() -> None:
    """An exact name pattern matches the rule's name."""
    meta = _stub_metadata("missing-module-docstring")
    assert matches_rule(meta, "missing-module-docstring") is True


def test_matches_rule_by_group() -> None:
    """A group pattern matches any rule in that group."""
    meta = _stub_metadata("missing-module-docstring")
    assert matches_rule(meta, "presence") is True


def test_matches_rule_no_match() -> None:
    """A pattern matching neither name nor group returns False."""
    meta = _stub_metadata("missing-module-docstring")
    assert matches_rule(meta, "prose") is False


# ---------------------------------------------------------------------------
# parse_inline_suppression
# ---------------------------------------------------------------------------


def test_parse_inline_suppression() -> None:
    """A line with a glossa: ignore= directive returns a tuple of rule names."""
    line = "def foo():  # glossa: ignore=non-imperative-summary,markdown-in-docstring"
    result = parse_inline_suppression(line)
    assert result == ("non-imperative-summary", "markdown-in-docstring")


def test_parse_inline_suppression_none() -> None:
    """A line without a suppression directive returns None."""
    line = "def foo():  # some unrelated comment"
    assert parse_inline_suppression(line) is None


# ---------------------------------------------------------------------------
# is_rule_suppressed
# ---------------------------------------------------------------------------


def test_is_rule_suppressed() -> None:
    """Returns True when the rule name is present in the suppressions tuple."""
    assert is_rule_suppressed("non-imperative-summary", ("non-imperative-summary", "markdown-in-docstring")) is True
    assert is_rule_suppressed("missing-period", ("non-imperative-summary", "markdown-in-docstring")) is False


# ---------------------------------------------------------------------------
# resolve_rule_policy
# ---------------------------------------------------------------------------


def _stub_metadata(name: str, group: str = "presence") -> RuleMetadata:
    from glossa.domain.contracts import ALL_TARGET_KINDS
    return RuleMetadata(
        name=name,
        group=group,
        description="stub",
        default_severity=Severity.WARNING,
        applies_to=ALL_TARGET_KINDS,
        fixable=False,
    )


def test_resolve_rule_policy_enabled(base_config: GlossaConfig) -> None:
    """A rule matching a pattern in the select list is enabled."""
    policy = resolve_rule_policy(_stub_metadata("missing-module-docstring"), "src/foo.py", base_config)
    assert policy.enabled is True


def test_resolve_rule_policy_ignored(base_config: GlossaConfig) -> None:
    """A rule present in the ignore list is disabled, even if also in select."""
    config = GlossaConfig(
        rules=RuleSelection(
            select=("presence",),
            ignore=("missing-module-docstring",),
            severity_overrides={},
            per_file_ignores={},
            rule_options={},
            section_order=DEFAULT_SECTION_ORDER,
        ),
        suppressions=base_config.suppressions,
        fix=base_config.fix,
        output=base_config.output,
        parsing=ParsingOptions(section_aliases={}),
    )
    policy = resolve_rule_policy(_stub_metadata("missing-module-docstring"), "src/foo.py", config)
    assert policy.enabled is False


def test_resolve_rule_policy_per_file(base_config: GlossaConfig) -> None:
    """per_file_ignores disables a rule for files matching the glob pattern."""
    config = GlossaConfig(
        rules=RuleSelection(
            select=("presence",),
            ignore=(),
            severity_overrides={},
            per_file_ignores={"src/legacy/*.py": ("missing-module-docstring",)},
            rule_options={},
            section_order=DEFAULT_SECTION_ORDER,
        ),
        suppressions=base_config.suppressions,
        fix=base_config.fix,
        output=base_config.output,
        parsing=ParsingOptions(section_aliases={}),
    )
    # Matching file: rule should be disabled
    policy_matching = resolve_rule_policy(_stub_metadata("missing-module-docstring"), "src/legacy/old.py", config)
    assert policy_matching.enabled is False

    # Non-matching file: rule should remain enabled
    policy_other = resolve_rule_policy(_stub_metadata("missing-module-docstring"), "src/new/fresh.py", config)
    assert policy_other.enabled is True
