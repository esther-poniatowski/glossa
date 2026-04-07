"""Tests for anti-pattern rules."""

from __future__ import annotations

from glossa.domain.contracts import (
    AttributeFact,
    ExceptionFact,
    ExtractedDocstring,
    ExtractedTarget,
    LintTarget,
    ModuleSymbolFact,
    ParameterFact,
    RelatedTargets,
    ResolvedRelatedTargets,
    RulePolicy,
    Severity,
    SignatureFacts,
    SourceRef,
    TargetKind,
    TextPosition,
    TextSpan,
    Visibility,
    WarningFact,
)
from glossa.domain.parsing import parse_docstring
from glossa.domain.rules import RuleContext
from glossa.domain.rules.anti_patterns import EmptyDocstring, RedundantReturnsNone, RstNoteWarningDirective, TrivialDunderDocstring


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_target(
    *,
    kind: TargetKind = TargetKind.FUNCTION,
    visibility: Visibility = Visibility.PUBLIC,
    is_test_target: bool = False,
    docstring=None,
    raw_docstring: ExtractedDocstring | None = None,
    signature: SignatureFacts | None = None,
    exceptions: tuple[ExceptionFact, ...] = (),
    warnings: tuple[WarningFact, ...] = (),
    attributes: tuple[AttributeFact, ...] = (),
    module_symbols: tuple[ModuleSymbolFact, ...] = (),
    decorators: tuple[str, ...] = (),
    related: ResolvedRelatedTargets | None = None,
    symbol_path: tuple[str, ...] = ("mymodule",),
) -> LintTarget:
    """Build a LintTarget with sensible defaults."""
    ref = SourceRef(source_id="mymodule.py", symbol_path=symbol_path)
    extracted = ExtractedTarget(
        ref=ref,
        kind=kind,
        visibility=visibility,
        is_test_target=is_test_target,
        docstring=raw_docstring,
        signature=signature,
        exceptions=exceptions,
        warnings=warnings,
        attributes=attributes,
        module_symbols=module_symbols,
        decorators=decorators,
        related=RelatedTargets(),
    )
    return LintTarget(
        extracted=extracted,
        docstring=docstring,
        related=related if related is not None else ResolvedRelatedTargets(),
    )


def make_context(options=None, *, rule=None):
    """Return a RuleContext with an enabled WARNING policy.

    When *rule* is provided, the option schema defaults are merged first,
    then any explicit *options* override them.
    """
    resolved: dict[str, object] = {}
    if rule is not None:
        resolved = {d.key: d.default for d in rule.metadata.option_schema}
    if options:
        resolved.update(options)
    return RuleContext(
        policy=RulePolicy(enabled=True, severity=Severity.WARNING, options=resolved)
    )


def parsed(text: str):
    """Parse a docstring body into a ParsedDocstring."""
    return parse_docstring(body=text, quote='"""', string_prefix="", indentation="    ")


# ---------------------------------------------------------------------------
# EmptyDocstring — empty-docstring
# ---------------------------------------------------------------------------


def test_empty_docstring_fires():
    """Docstring with empty/whitespace-only body fires."""
    raw = ExtractedDocstring(
        body="   ",
        quote='"""',
        string_prefix="",
        indentation="    ",
        body_span=TextSpan(
            start=TextPosition(line=1, column=0),
            end=TextPosition(line=1, column=3),
        ),
        literal_span=TextSpan(
            start=TextPosition(line=1, column=0),
            end=TextPosition(line=1, column=9),
        ),
    )
    target = make_target(raw_docstring=raw, docstring=None)
    diagnostics = EmptyDocstring().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "empty-docstring"


def test_empty_docstring_nonempty_no_fire():
    """Docstring with actual content does not fire."""
    raw = ExtractedDocstring(
        body="Do something.",
        quote='"""',
        string_prefix="",
        indentation="    ",
        body_span=TextSpan(
            start=TextPosition(line=1, column=0),
            end=TextPosition(line=1, column=13),
        ),
        literal_span=TextSpan(
            start=TextPosition(line=1, column=0),
            end=TextPosition(line=1, column=19),
        ),
    )
    target = make_target(raw_docstring=raw, docstring=parsed("Do something."))
    diagnostics = EmptyDocstring().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# TrivialDunderDocstring — trivial-dunder-docstring
# ---------------------------------------------------------------------------


def test_trivial_dunder_docstring_init_fires():
    """Dunder __init__ with boilerplate summary fires."""
    rule = TrivialDunderDocstring()
    target = make_target(
        kind=TargetKind.METHOD,
        docstring=parsed("Initialize self."),
        symbol_path=("MyClass", "__init__"),
    )
    diagnostics = rule.evaluate(target, make_context(rule=rule))
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "trivial-dunder-docstring"


def test_trivial_dunder_docstring_real_summary_no_fire():
    """Dunder __init__ with a meaningful summary does not fire."""
    rule = TrivialDunderDocstring()
    target = make_target(
        kind=TargetKind.METHOD,
        docstring=parsed("Set up the database connection."),
        symbol_path=("MyClass", "__init__"),
    )
    diagnostics = rule.evaluate(target, make_context(rule=rule))
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# RedundantReturnsNone — redundant-returns-none
# ---------------------------------------------------------------------------


def _make_void_sig() -> SignatureFacts:
    return SignatureFacts(
        parameters=(),
        return_annotation="None",
        returns_value=False,
        yields_value=False,
    )


def _make_returning_sig() -> SignatureFacts:
    return SignatureFacts(
        parameters=(),
        return_annotation="int",
        returns_value=True,
        yields_value=False,
    )


def test_redundant_returns_none_void_fires():
    """Void function with Returns section listing None fires."""
    doc_text = (
        "Do something.\n\n"
        "Returns\n"
        "-------\n"
        "None\n"
        "    Nothing.\n"
    )
    target = make_target(
        docstring=parsed(doc_text),
        signature=_make_void_sig(),
    )
    diagnostics = RedundantReturnsNone().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "redundant-returns-none"


def test_redundant_returns_none_returning_no_fire():
    """Function that returns a value with Returns section does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Returns\n"
        "-------\n"
        "int\n"
        "    The result.\n"
    )
    target = make_target(
        docstring=parsed(doc_text),
        signature=_make_returning_sig(),
    )
    diagnostics = RedundantReturnsNone().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# RstNoteWarningDirective — rst-note-warning-directive
# ---------------------------------------------------------------------------


def test_rst_note_warning_directive_note_fires():
    """Docstring with ``.. note::`` directive fires."""
    doc_text = (
        "Do something.\n\n"
        ".. note::\n"
        "    This is important.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = RstNoteWarningDirective().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "rst-note-warning-directive"


def test_rst_note_warning_directive_numpy_notes_no_fire():
    """Docstring with a proper NumPy Notes section does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Notes\n"
        "-----\n"
        "This is important.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = RstNoteWarningDirective().evaluate(target, make_context())
    assert diagnostics == ()
