"""Tests for source-level fix application."""

from __future__ import annotations

from glossa.application.contracts import (
    FixApplyMode,
    FixPolicy,
    GlossaConfig,
    OutputFormat,
    OutputOptions,
    RuleSelection,
    SuppressionPolicy,
)
from glossa.application.fixing import FixRejectionReason, apply_fixes
from glossa.application.linting import analyze_file
from glossa.application.registry import RuleRegistry
from glossa.domain.rules.prose import D201
from glossa.infrastructure.extraction import ASTExtractor
from glossa.infrastructure.files import LocalFilePort


def _config() -> GlossaConfig:
    return GlossaConfig(
        rules=RuleSelection(
            select=("D201",),
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
            enabled=True,
            apply=FixApplyMode.SAFE,
            validate_after_apply=True,
        ),
        output=OutputOptions(
            format=OutputFormat.TEXT,
            color=False,
            show_source=True,
        ),
    )


def test_apply_fixes_updates_docstring_body_without_corrupting_file(tmp_path) -> None:
    source = 'x = 1\n\ndef render():\n    """summary without period"""\n    return 1\n'
    path = tmp_path / "sample.py"
    path.write_text(source, encoding="utf-8")

    config = _config()
    analyzed = analyze_file(
        source_id="sample.py",
        source_text=source,
        extraction_port=ASTExtractor(),
        config=config,
        registry=RuleRegistry(builtins=(D201(),), plugins=()),
    )

    results = apply_fixes(
        analyzed_files=(analyzed,),
        file_port=LocalFilePort(tmp_path),
        config=config,
        extraction_port=ASTExtractor(),
        registry=RuleRegistry(builtins=(D201(),), plugins=()),
    )

    assert results[0].applied
    assert results[0].rejected == ()
    assert (
        path.read_text(encoding="utf-8")
        == 'x = 1\n\ndef render():\n    """summary without period."""\n    return 1\n'
    )


def test_apply_fixes_does_not_false_conflict_across_multiple_docstrings(tmp_path) -> None:
    source = (
        'def a():\n'
        '    """first summary"""\n'
        "    return 1\n\n"
        'def b():\n'
        '    """second summary"""\n'
        "    return 2\n"
    )
    path = tmp_path / "sample.py"
    path.write_text(source, encoding="utf-8")

    config = _config()
    analyzed = analyze_file(
        source_id="sample.py",
        source_text=source,
        extraction_port=ASTExtractor(),
        config=config,
        registry=RuleRegistry(builtins=(D201(),), plugins=()),
    )

    results = apply_fixes(
        analyzed_files=(analyzed,),
        file_port=LocalFilePort(tmp_path),
        config=config,
        extraction_port=ASTExtractor(),
        registry=RuleRegistry(builtins=(D201(),), plugins=()),
    )

    assert len(results[0].applied) == 2
    assert not any(
        rejection.reason is FixRejectionReason.CONFLICT
        for rejection in results[0].rejected
    )
    assert (
        path.read_text(encoding="utf-8")
        == (
            'def a():\n'
            '    """first summary."""\n'
            "    return 1\n\n"
            'def b():\n'
            '    """second summary."""\n'
            "    return 2\n"
        )
    )
