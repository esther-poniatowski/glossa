"""Tests for glossa.adapters.formatters."""

from __future__ import annotations

import json

import pytest

from glossa.application.contracts import (
    Diagnostic,
    FixPlan,
    Severity,
    SourceRef,
    TextPosition,
    TextSpan,
)
from glossa.adapters.formatters import format_json, format_text


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _source_ref(source_id: str = "src/foo.py", symbol_path: tuple[str, ...] = ("MyClass",)) -> SourceRef:
    return SourceRef(source_id=source_id, symbol_path=symbol_path)


def _span(start_line: int = 1, start_col: int = 0, end_line: int = 1, end_col: int = 10) -> TextSpan:
    return TextSpan(
        start=TextPosition(line=start_line, column=start_col),
        end=TextPosition(line=end_line, column=end_col),
    )


def _diagnostic(
    code: str = "D100",
    message: str = "Missing docstring.",
    severity: Severity = Severity.WARNING,
    source_id: str = "src/foo.py",
    symbol_path: tuple[str, ...] = ("MyClass",),
    span: TextSpan | None = None,
    fix: FixPlan | None = None,
) -> Diagnostic:
    return Diagnostic(
        code=code,
        message=message,
        severity=severity,
        target=_source_ref(source_id, symbol_path),
        span=span,
        fix=fix,
    )


def _fix_plan(source_id: str = "src/foo.py") -> FixPlan:
    return FixPlan(
        description="Add missing docstring",
        target=_source_ref(source_id),
        edits=(),
        affected_rules=("D100",),
    )


# ---------------------------------------------------------------------------
# format_text
# ---------------------------------------------------------------------------


def test_format_text_empty() -> None:
    """No diagnostics returns the 'All checks passed.' sentinel string."""
    result = format_text([])
    assert result == "All checks passed."


def test_format_text_single() -> None:
    """A single diagnostic is formatted with its code, message, and severity."""
    diag = _diagnostic(
        code="D200",
        message="One-line docstring should fit on one line.",
        severity=Severity.WARNING,
        span=_span(3, 4, 3, 40),
    )
    result = format_text([diag], )

    assert "D200" in result
    assert "One-line docstring should fit on one line." in result
    assert "WARNING" in result


def test_format_text_fixable() -> None:
    """A diagnostic with a fix plan includes '(fixable)' in the output."""
    diag = _diagnostic(
        code="D100",
        message="Missing docstring in public module.",
        fix=_fix_plan(),
    )
    result = format_text([diag], )
    assert "(fixable)" in result


# ---------------------------------------------------------------------------
# format_json
# ---------------------------------------------------------------------------


def test_format_json_empty() -> None:
    """No diagnostics returns valid JSON with count equal to 0."""
    result = format_json([])
    data = json.loads(result)

    assert data["count"] == 0
    assert data["diagnostics"] == []


def test_format_json_single() -> None:
    """A single diagnostic produces the expected JSON structure."""
    diag = _diagnostic(
        code="D300",
        message="Use triple double quotes.",
        severity=Severity.CONVENTION,
        source_id="src/bar.py",
        symbol_path=("helper",),
        span=_span(5, 0, 5, 20),
    )
    result = format_json([diag])
    data = json.loads(result)

    assert data["count"] == 1
    item = data["diagnostics"][0]
    assert item["code"] == "D300"
    assert item["message"] == "Use triple double quotes."
    assert item["severity"] == "convention"
    assert item["source_id"] == "src/bar.py"
    assert item["symbol_path"] == ["helper"]
    assert item["location"]["start_line"] == 5
    assert item["fixable"] is False


def test_format_json_roundtrip() -> None:
    """json.loads(format_json(...)) produces a valid dict with the expected top-level keys."""
    diagnostics = [
        _diagnostic("D100", "Missing module docstring.", Severity.WARNING),
        _diagnostic("D200", "One-liner too long.", Severity.CONVENTION),
    ]
    result = format_json(diagnostics)
    data = json.loads(result)

    assert isinstance(data, dict)
    assert "diagnostics" in data
    assert "count" in data
    assert data["count"] == 2
    assert len(data["diagnostics"]) == 2
