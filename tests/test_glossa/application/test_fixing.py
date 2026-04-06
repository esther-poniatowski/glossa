"""Tests for source-level fix application."""

from __future__ import annotations

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
from glossa.application.fixing import FixRejectionReason, apply_fixes
from glossa.application.linting import analyze_file
from glossa.application.registry import RuleRegistry
from glossa.domain.rules.prose import D201
from glossa.infrastructure.extraction import ASTExtractor


def _config() -> GlossaConfig:
    return GlossaConfig(
        rules=RuleSelection(
            select=("missing-period",),
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
            enabled=True,
            apply=FixApplyMode.SAFE,
            validate_after_apply=False,
        ),
        output=OutputOptions(
            format=OutputFormat.TEXT,
            color=False,
            show_source=True,
        ),
        parsing=ParsingOptions(section_aliases={}),
    )


def test_apply_fixes_updates_docstring_body_without_corrupting_file() -> None:
    source = 'x = 1\n\ndef render():\n    """summary without period"""\n    return 1\n'

    config = _config()
    analyzed = analyze_file(
        source_id="sample.py",
        source_text=source,
        extraction_port=ASTExtractor(),
        config=config,
        registry=RuleRegistry(builtins=(D201(),), plugins=()),
    )

    transformations = apply_fixes(analyzed_files=(analyzed,), config=config)

    assert len(transformations) == 1
    t = transformations[0]
    assert t.accepted
    assert t.rejected == ()
    assert (
        t.edited_source
        == 'x = 1\n\ndef render():\n    """summary without period."""\n    return 1\n'
    )


def test_apply_fixes_does_not_false_conflict_across_multiple_docstrings() -> None:
    source = (
        'def a():\n'
        '    """first summary"""\n'
        "    return 1\n\n"
        'def b():\n'
        '    """second summary"""\n'
        "    return 2\n"
    )

    config = _config()
    analyzed = analyze_file(
        source_id="sample.py",
        source_text=source,
        extraction_port=ASTExtractor(),
        config=config,
        registry=RuleRegistry(builtins=(D201(),), plugins=()),
    )

    transformations = apply_fixes(analyzed_files=(analyzed,), config=config)

    assert len(transformations) == 1
    t = transformations[0]
    assert len(t.accepted) == 2
    assert not any(
        rejection.reason is FixRejectionReason.CONFLICT
        for rejection in t.rejected
    )
    assert (
        t.edited_source
        == (
            'def a():\n'
            '    """first summary."""\n'
            "    return 1\n\n"
            'def b():\n'
            '    """second summary."""\n'
            "    return 2\n"
        )
    )
