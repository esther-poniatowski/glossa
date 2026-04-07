"""Tests for D3xx section structure and placement rules."""

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
    D300,
    D301,
    D302,
    D303,
    D304,
    D305,
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
    """Return a RuleContext with section order for D301 tests."""
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
# D300 -- malformed-underline
# ---------------------------------------------------------------------------


def test_d300_correct_underline():
    """Section with correctly sized dash underline does not fire D300."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "----------\n"
        "x : int\n"
        "    The value.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D300().evaluate(target, make_context())
    assert diagnostics == ()


def test_d300_wrong_underline_length():
    """Section with wrong underline length fires D300."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "-----\n"
        "x : int\n"
        "    The value.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D300().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "malformed-underline"


# ---------------------------------------------------------------------------
# D301 -- section-order
# ---------------------------------------------------------------------------


def test_d301_correct_order():
    """Sections in canonical NumPy order do not fire D301."""
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
    diagnostics = D301().evaluate(target, make_context_with_section_order())
    assert diagnostics == ()


def test_d301_reversed_order():
    """Returns before Parameters fires D301."""
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
    diagnostics = D301().evaluate(target, make_context_with_section_order())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "section-order"


# ---------------------------------------------------------------------------
# D302 -- undocumented-parameter
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


def test_d302_all_params_documented():
    """All signature parameters documented in docstring does not fire D302."""
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
    diagnostics = D302().evaluate(target, make_context())
    assert diagnostics == ()


def test_d302_missing_param():
    """Parameter in signature but missing from docstring fires D302."""
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
    diagnostics = D302().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "undocumented-parameter"


# ---------------------------------------------------------------------------
# D303 -- extraneous-parameter
# ---------------------------------------------------------------------------


def test_d303_extra_param_in_docstring():
    """Parameter in docstring but not in signature fires D303."""
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
    diagnostics = D303().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "extraneous-parameter"


# ---------------------------------------------------------------------------
# D304 -- malformed-deprecation
# ---------------------------------------------------------------------------


def test_d304_deprecation_missing_version():
    """Deprecation directive without a version fires D304."""
    doc_text = (
        "Do something.\n\n"
        ".. deprecated::\n"
        "    Use something else.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D304().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "malformed-deprecation"


# ---------------------------------------------------------------------------
# D305 -- rst-directive-instead-of-section
# ---------------------------------------------------------------------------


def test_d305_rst_hint_directive():
    """An RST ``.. hint::`` directive fires D305."""
    doc_text = (
        "Do something.\n\n"
        ".. hint::\n"
        "    This is a hint.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D305().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "rst-directive-instead-of-section"


def test_d305_proper_numpy_notes_section():
    """A proper NumPy Notes section does not fire D305."""
    doc_text = (
        "Do something.\n\n"
        "Notes\n"
        "-----\n"
        "This is a note.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D305().evaluate(target, make_context())
    assert diagnostics == ()
