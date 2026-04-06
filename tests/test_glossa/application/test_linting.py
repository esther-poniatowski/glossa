"""Tests for application-level lint analysis."""

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
from glossa.application.linting import analyze_file
from glossa.application.registry import RuleRegistry
from glossa.domain.rules.presence import D100, D102
from glossa.infrastructure.extraction import ASTExtractor


def _config(*select: str) -> GlossaConfig:
    return GlossaConfig(
        rules=RuleSelection(
            select=select,
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
            validate_after_apply=True,
        ),
        output=OutputOptions(
            format=OutputFormat.TEXT,
            color=False,
            show_source=True,
        ),
        parsing=ParsingOptions(section_aliases={}),
    )


def test_definition_line_suppression_disables_missing_docstring_rule() -> None:
    source = "def render():  # glossa: ignore=missing-callable-docstring\n    return 1\n"

    analyzed = analyze_file(
        source_id="sample.py",
        source_text=source,
        extraction_port=ASTExtractor(),
        config=_config("missing-callable-docstring"),
        registry=RuleRegistry(builtins=(D102(),), plugins=()),
    )

    assert analyzed.diagnostics == ()


def test_module_header_suppression_disables_missing_module_docstring_rule() -> None:
    source = "# glossa: ignore=missing-module-docstring\nx = 1\n"

    analyzed = analyze_file(
        source_id="sample.py",
        source_text=source,
        extraction_port=ASTExtractor(),
        config=_config("missing-module-docstring"),
        registry=RuleRegistry(builtins=(D100(),), plugins=()),
    )

    assert analyzed.diagnostics == ()
