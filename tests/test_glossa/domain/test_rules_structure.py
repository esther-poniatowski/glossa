"""Tests for section structure and placement rules."""

from __future__ import annotations

from glossa.application.configuration import DEFAULT_SECTION_ORDER
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
    Visibility,
    WarningFact,
)
from glossa.domain.parsing import parse_docstring
from glossa.domain.rules import RuleContext
from glossa.domain.rules.structure import (
    ExtraneousParameter,
    MalformedDeprecation,
    MalformedUnderline,
    RstDirectiveInsteadOfSection,
    SectionOrder,
    UndocumentedParameter,
)


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
) -> LintTarget:
    """Build a LintTarget with sensible defaults."""
    ref = SourceRef(source_id="mymodule.py", symbol_path=("mymodule",))
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


def make_context(options: dict | None = None) -> RuleContext:
    """Return a RuleContext with an enabled WARNING policy."""
    return RuleContext(
        policy=RulePolicy(
            enabled=True,
            severity=Severity.WARNING,
            options=options or {},
        )
    )


def make_context_with_section_order(options: dict | None = None) -> RuleContext:
    """Return a RuleContext with section order for SectionOrder tests."""
    return RuleContext(
        policy=RulePolicy(
            enabled=True,
            severity=Severity.WARNING,
            options=options or {},
        ),
        section_order=DEFAULT_SECTION_ORDER,
    )


def parsed(text: str):
    """Parse a docstring body into a ParsedDocstring."""
    return parse_docstring(body=text, quote='"""', string_prefix="", indentation="    ")


# ---------------------------------------------------------------------------
# MalformedUnderline -- malformed-underline
# ---------------------------------------------------------------------------


def test_malformed_underline_correct_no_fire():
    """Section with correctly sized dash underline does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "----------\n"
        "x : int\n"
        "    The value.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = MalformedUnderline().evaluate(target, make_context())
    assert diagnostics == ()


def test_malformed_underline_wrong_length_fires():
    """Section with wrong underline length fires."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "-----\n"
        "x : int\n"
        "    The value.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = MalformedUnderline().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "malformed-underline"


# ---------------------------------------------------------------------------
# SectionOrder -- section-order
# ---------------------------------------------------------------------------


def test_section_order_correct_no_fire():
    """Sections in canonical NumPy order do not fire."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "----------\n"
        "x : int\n"
        "    The value.\n"
        "\n"
        "Returns\n"
        "-------\n"
        "int\n"
        "    The result.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = SectionOrder().evaluate(target, make_context_with_section_order())
    assert diagnostics == ()


def test_section_order_reversed_fires():
    """Returns before Parameters fires."""
    doc_text = (
        "Do something.\n\n"
        "Returns\n"
        "-------\n"
        "int\n"
        "    The result.\n"
        "\n"
        "Parameters\n"
        "----------\n"
        "x : int\n"
        "    The value.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = SectionOrder().evaluate(target, make_context_with_section_order())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "section-order"


# ---------------------------------------------------------------------------
# UndocumentedParameter -- undocumented-parameter
# ---------------------------------------------------------------------------


def _make_sig(*names: str) -> SignatureFacts:
    return SignatureFacts(
        parameters=tuple(
            ParameterFact(
                name=n,
                annotation="int",
                default=None,
                kind="positional_or_keyword",
            )
            for n in names
        ),
        returns_value=True,
        return_annotation="int",
        yields_value=False,
    )


def test_undocumented_parameter_all_documented_no_fire():
    """All signature parameters documented in docstring does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "----------\n"
        "x : int\n"
        "    The value.\n"
    )
    target = make_target(
        docstring=parsed(doc_text),
        signature=_make_sig("x"),
    )
    diagnostics = UndocumentedParameter().evaluate(target, make_context())
    assert diagnostics == ()


def test_undocumented_parameter_missing_fires():
    """Parameter in signature but missing from docstring fires."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "----------\n"
        "x : int\n"
        "    The value.\n"
    )
    target = make_target(
        docstring=parsed(doc_text),
        signature=_make_sig("x", "y"),
    )
    diagnostics = UndocumentedParameter().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "undocumented-parameter"


# ---------------------------------------------------------------------------
# ExtraneousParameter -- extraneous-parameter
# ---------------------------------------------------------------------------


def test_extraneous_parameter_fires():
    """Parameter in docstring but not in signature fires."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "----------\n"
        "x : int\n"
        "    The value.\n"
        "y : int\n"
        "    Extra param.\n"
    )
    target = make_target(
        docstring=parsed(doc_text),
        signature=_make_sig("x"),
    )
    diagnostics = ExtraneousParameter().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "extraneous-parameter"


# ---------------------------------------------------------------------------
# MalformedDeprecation -- malformed-deprecation
# ---------------------------------------------------------------------------


def test_malformed_deprecation_missing_version_fires():
    """Deprecation directive without a version fires."""
    doc_text = (
        "Do something.\n\n"
        ".. deprecated::\n"
        "    Use something else.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = MalformedDeprecation().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "malformed-deprecation"


# ---------------------------------------------------------------------------
# RstDirectiveInsteadOfSection -- rst-directive-instead-of-section
# ---------------------------------------------------------------------------


def test_rst_directive_instead_of_section_hint_fires():
    """An RST ``.. hint::`` directive fires."""
    doc_text = (
        "Do something.\n\n"
        ".. hint::\n"
        "    This is a hint.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = RstDirectiveInsteadOfSection().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "rst-directive-instead-of-section"


def test_rst_directive_instead_of_section_numpy_notes_no_fire():
    """A proper NumPy Notes section does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Notes\n"
        "-----\n"
        "This is a note.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = RstDirectiveInsteadOfSection().evaluate(target, make_context())
    assert diagnostics == ()
