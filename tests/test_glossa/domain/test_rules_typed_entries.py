"""Tests for typed entry consistency rules."""

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
from glossa.domain.rules.typed_entries import MissingParamType, ParamTypeMismatch, ReturnTypeMismatch


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


def make_context(options: dict | None = None, *, rule=None) -> RuleContext:
    """Return a RuleContext with an enabled WARNING policy."""
    resolved: dict[str, object] = {}
    if rule is not None:
        resolved = {d.key: d.default for d in rule.metadata.option_schema}
    if options:
        resolved.update(options)
    return RuleContext(
        policy=RulePolicy(
            enabled=True,
            severity=Severity.WARNING,
            options=resolved,
        )
    )


def parsed(text: str):
    """Parse a docstring body into a ParsedDocstring."""
    return parse_docstring(body=text, quote='"""', string_prefix="", indentation="    ")


# ---------------------------------------------------------------------------
# Shared signature helpers
# ---------------------------------------------------------------------------


def _make_sig_with_param(name: str = "x", annotation: str | None = "int") -> SignatureFacts:
    return SignatureFacts(
        parameters=(
            ParameterFact(
                name=name,
                annotation=annotation,
                default=None,
                kind="positional_or_keyword",
            ),
        ),
        return_annotation=None,
        returns_value=False,
        yields_value=False,
    )


def _make_sig_with_return(return_annotation: str = "list") -> SignatureFacts:
    return SignatureFacts(
        parameters=(),
        return_annotation=return_annotation,
        returns_value=True,
        yields_value=False,
    )


# ---------------------------------------------------------------------------
# MissingParamType — missing-param-type
# ---------------------------------------------------------------------------


def test_missing_param_type_fires():
    """Parameter with annotation but no type in docstring fires."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "----------\n"
        "x\n"
        "    The input.\n"
    )
    target = make_target(
        docstring=parsed(doc_text),
        signature=_make_sig_with_param("x", "int"),
    )
    diagnostics = MissingParamType().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "missing-param-type"


def test_missing_param_type_present_no_fire():
    """Parameter with annotation and matching type in docstring does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "----------\n"
        "x : int\n"
        "    The input.\n"
    )
    target = make_target(
        docstring=parsed(doc_text),
        signature=_make_sig_with_param("x", "int"),
    )
    diagnostics = MissingParamType().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# ParamTypeMismatch — param-type-mismatch
# ---------------------------------------------------------------------------


def test_param_type_mismatch_fires():
    """Parameter type in docstring differs from annotation fires."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "----------\n"
        "x : str\n"
        "    The input.\n"
    )
    target = make_target(
        docstring=parsed(doc_text),
        signature=_make_sig_with_param("x", "int"),
    )
    diagnostics = ParamTypeMismatch().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "param-type-mismatch"


def test_param_type_mismatch_matching_no_fire():
    """Parameter type matching annotation does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "----------\n"
        "x : int\n"
        "    The input.\n"
    )
    target = make_target(
        docstring=parsed(doc_text),
        signature=_make_sig_with_param("x", "int"),
    )
    diagnostics = ParamTypeMismatch().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# ReturnTypeMismatch — return-type-mismatch
# ---------------------------------------------------------------------------


def test_return_type_mismatch_fires():
    """Returns type in docstring differs from annotation fires."""
    doc_text = (
        "Do something.\n\n"
        "Returns\n"
        "-------\n"
        "tuple\n"
        "    The result.\n"
    )
    target = make_target(
        docstring=parsed(doc_text),
        signature=_make_sig_with_return("list"),
    )
    diagnostics = ReturnTypeMismatch().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "return-type-mismatch"


def test_return_type_mismatch_matching_no_fire():
    """Returns type matching annotation does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Returns\n"
        "-------\n"
        "list\n"
        "    The result.\n"
    )
    target = make_target(
        docstring=parsed(doc_text),
        signature=_make_sig_with_return("list"),
    )
    diagnostics = ReturnTypeMismatch().evaluate(target, make_context())
    assert diagnostics == ()
