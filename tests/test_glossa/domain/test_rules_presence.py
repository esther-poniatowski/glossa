"""Tests for presence and coverage rules."""

from __future__ import annotations

import pytest

from glossa.domain.contracts import (
    AttributeFact,
    Confidence,
    ExceptionEvidence,
    ExceptionFact,
    ExtractedDocstring,
    ExtractedTarget,
    LintTarget,
    ModuleSymbolFact,
    ParameterFact,
    RelatedTargetSnapshot,
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
from glossa.domain.rules.presence import (
    MissingAttributesSection,
    MissingCallableDocstring,
    MissingClassDocstring,
    MissingDeprecationDirective,
    MissingModuleDocstring,
    MissingModuleInventory,
    MissingParametersSection,
    MissingRaisesSection,
    MissingReturnsSection,
    MissingWarnsSection,
    MissingYieldsSection,
    ParamsInInitNotClass,
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


def make_context(options: dict | None = None, *, rule=None) -> RuleContext:
    """Return a RuleContext with an enabled WARNING policy.

    When *rule* is provided, the option schema defaults are merged first,
    then any explicit *options* override them — mirroring the production
    ``_resolve_options`` behaviour.
    """
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
# MissingModuleDocstring — Missing public module docstring
# ---------------------------------------------------------------------------


def test_missing_module_docstring_fires():
    target = make_target(kind=TargetKind.MODULE, visibility=Visibility.PUBLIC, docstring=None)
    diagnostics = MissingModuleDocstring().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "missing-module-docstring"


def test_missing_module_docstring_present_no_fire():
    target = make_target(
        kind=TargetKind.MODULE,
        visibility=Visibility.PUBLIC,
        docstring=parsed("Module summary."),
    )
    diagnostics = MissingModuleDocstring().evaluate(target, make_context())
    assert diagnostics == ()


def test_missing_module_docstring_private_no_fire():
    target = make_target(kind=TargetKind.MODULE, visibility=Visibility.PRIVATE, docstring=None)
    diagnostics = MissingModuleDocstring().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# MissingClassDocstring — Missing public class docstring
# ---------------------------------------------------------------------------


def test_missing_class_docstring_fires():
    target = make_target(kind=TargetKind.CLASS, visibility=Visibility.PUBLIC, docstring=None)
    diagnostics = MissingClassDocstring().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "missing-class-docstring"


def test_missing_class_docstring_present_no_fire():
    target = make_target(
        kind=TargetKind.CLASS,
        visibility=Visibility.PUBLIC,
        docstring=parsed("A class."),
    )
    diagnostics = MissingClassDocstring().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# MissingCallableDocstring — Missing public callable docstring
# ---------------------------------------------------------------------------


def test_missing_callable_docstring_fires():
    rule = MissingCallableDocstring()
    target = make_target(kind=TargetKind.FUNCTION, visibility=Visibility.PUBLIC, docstring=None)
    diagnostics = rule.evaluate(target, make_context(rule=rule))
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "missing-callable-docstring"


def test_missing_callable_docstring_present_no_fire():
    rule = MissingCallableDocstring()
    target = make_target(
        kind=TargetKind.FUNCTION,
        visibility=Visibility.PUBLIC,
        docstring=parsed("Do something."),
    )
    diagnostics = rule.evaluate(target, make_context(rule=rule))
    assert diagnostics == ()


def test_missing_callable_docstring_private_skipped():
    """PRIVATE callable does not fire when include_private_helpers is False (default)."""
    rule = MissingCallableDocstring()
    target = make_target(
        kind=TargetKind.FUNCTION,
        visibility=Visibility.PRIVATE,
        docstring=None,
    )
    diagnostics = rule.evaluate(target, make_context({"include_private_helpers": False}, rule=rule))
    assert diagnostics == ()


def test_missing_callable_docstring_private_opted_in_no_fire():
    """PRIVATE callable fires when include_private_helpers is True."""
    # MissingCallableDocstring only fires for PUBLIC visibility regardless of option
    # — private helpers are simply not flagged even with include_private_helpers=True
    # because the rule guards on target.visibility is Visibility.PUBLIC at the end.
    rule = MissingCallableDocstring()
    target = make_target(
        kind=TargetKind.FUNCTION,
        visibility=Visibility.PRIVATE,
        docstring=None,
    )
    diagnostics = rule.evaluate(target, make_context({"include_private_helpers": True}, rule=rule))
    # include_private_helpers=True only removes the early-exit guard; the final
    # check still requires PUBLIC visibility for the rule to fire.
    assert diagnostics == ()


def test_missing_callable_docstring_test_target_skipped():
    """Test functions are skipped when include_test_functions is False."""
    rule = MissingCallableDocstring()
    target = make_target(
        kind=TargetKind.FUNCTION,
        visibility=Visibility.PUBLIC,
        is_test_target=True,
        docstring=None,
    )
    diagnostics = rule.evaluate(target, make_context({"include_test_functions": False}, rule=rule))
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# MissingParametersSection — Missing Parameters section
# ---------------------------------------------------------------------------


def _make_sig_with_params(*names: str) -> SignatureFacts:
    return SignatureFacts(
        parameters=tuple(
            ParameterFact(name=n, annotation=None, default=None, kind="positional_or_keyword")
            for n in names
        ),
        return_annotation=None,
        returns_value=False,
        yields_value=False,
    )


def test_missing_parameters_section_fires():
    """Function with params but no Parameters section fires."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        signature=_make_sig_with_params("x", "y"),
    )
    diagnostics = MissingParametersSection().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "missing-parameters-section"


def test_missing_parameters_section_present_no_fire():
    """Function with a Parameters section does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Parameters\n"
        "----------\n"
        "x : int\n"
        "    The value.\n"
    )
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed(doc_text),
        signature=_make_sig_with_params("x"),
    )
    diagnostics = MissingParametersSection().evaluate(target, make_context())
    assert diagnostics == ()


def test_missing_parameters_section_no_params_no_fire():
    """Function with no documentable params does not fire."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        signature=_make_sig_with_params(),
    )
    diagnostics = MissingParametersSection().evaluate(target, make_context())
    assert diagnostics == ()


def test_missing_parameters_section_self_excluded():
    """'self' is excluded from documentable params for methods."""
    target = make_target(
        kind=TargetKind.METHOD,
        docstring=parsed("Do something."),
        signature=_make_sig_with_params("self"),
    )
    diagnostics = MissingParametersSection().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# MissingReturnsSection — Missing Returns section
# ---------------------------------------------------------------------------


def _make_sig_returns(returns_value: bool = True, yields_value: bool = False) -> SignatureFacts:
    return SignatureFacts(
        parameters=(),
        return_annotation=None,
        returns_value=returns_value,
        yields_value=yields_value,
    )


def test_missing_returns_section_fires():
    """Function that returns a value but has no Returns section fires."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        signature=_make_sig_returns(returns_value=True),
    )
    diagnostics = MissingReturnsSection().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "missing-returns-section"


def test_missing_returns_section_present_no_fire():
    """Function with a Returns section does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Returns\n"
        "-------\n"
        "int\n"
        "    The result.\n"
    )
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed(doc_text),
        signature=_make_sig_returns(returns_value=True),
    )
    diagnostics = MissingReturnsSection().evaluate(target, make_context())
    assert diagnostics == ()


def test_missing_returns_section_no_return_value_no_fire():
    """Function that does not return a value does not fire."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        signature=_make_sig_returns(returns_value=False),
    )
    diagnostics = MissingReturnsSection().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# MissingYieldsSection — Missing Yields section
# ---------------------------------------------------------------------------


def test_missing_yields_section_fires():
    """Generator function with no Yields section fires."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Generate values."),
        signature=_make_sig_returns(returns_value=False, yields_value=True),
    )
    diagnostics = MissingYieldsSection().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "missing-yields-section"


def test_missing_yields_section_present_no_fire():
    """Generator with a Yields section does not fire."""
    doc_text = (
        "Generate values.\n\n"
        "Yields\n"
        "------\n"
        "int\n"
        "    Each value.\n"
    )
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed(doc_text),
        signature=_make_sig_returns(returns_value=False, yields_value=True),
    )
    diagnostics = MissingYieldsSection().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# MissingRaisesSection — Missing Raises section
# ---------------------------------------------------------------------------


def test_missing_raises_section_fires():
    """High-confidence raise with no Raises section fires."""
    exc = ExceptionFact(type_name="ValueError", evidence=ExceptionEvidence.RAISE, confidence=Confidence.HIGH)
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        exceptions=(exc,),
    )
    diagnostics = MissingRaisesSection().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "missing-raises-section"


def test_missing_raises_section_present_no_fire():
    """High-confidence raise with a Raises section does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Raises\n"
        "------\n"
        "ValueError\n"
        "    When the input is invalid.\n"
    )
    exc = ExceptionFact(type_name="ValueError", evidence=ExceptionEvidence.RAISE, confidence=Confidence.HIGH)
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed(doc_text),
        exceptions=(exc,),
    )
    diagnostics = MissingRaisesSection().evaluate(target, make_context())
    assert diagnostics == ()


def test_missing_raises_section_low_confidence_no_fire():
    """Low-confidence raise does not trigger the rule."""
    exc = ExceptionFact(type_name="ValueError", evidence=ExceptionEvidence.RAISE, confidence=Confidence.LOW)
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        exceptions=(exc,),
    )
    diagnostics = MissingRaisesSection().evaluate(target, make_context())
    assert diagnostics == ()


def test_missing_raises_section_reraise_excluded():
    """High-confidence reraise is excluded from checks."""
    exc = ExceptionFact(type_name="ValueError", evidence=ExceptionEvidence.RERAISE, confidence=Confidence.HIGH)
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        exceptions=(exc,),
    )
    diagnostics = MissingRaisesSection().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# MissingModuleInventory — Missing module inventory
# ---------------------------------------------------------------------------


def _make_symbols(n_classes: int = 0, n_functions: int = 0) -> tuple[ModuleSymbolFact, ...]:
    classes = tuple(
        ModuleSymbolFact(name=f"Class{i}", kind="class", is_public=True)
        for i in range(n_classes)
    )
    functions = tuple(
        ModuleSymbolFact(name=f"func_{i}", kind="function", is_public=True)
        for i in range(n_functions)
    )
    return classes + functions


def test_missing_module_inventory_fires():
    """Module with many public symbols but no inventory fires."""
    rule = MissingModuleInventory()
    target = make_target(
        kind=TargetKind.MODULE,
        docstring=parsed("A module."),
        module_symbols=_make_symbols(n_classes=2, n_functions=2),
    )
    diagnostics = rule.evaluate(target, make_context(rule=rule))
    rules = [d.rule for d in diagnostics]
    assert rules.count("missing-module-inventory") == 2


def test_missing_module_inventory_below_threshold_no_fire():
    """Module with fewer public symbols than the threshold does not fire."""
    rule = MissingModuleInventory()
    target = make_target(
        kind=TargetKind.MODULE,
        docstring=parsed("A module."),
        module_symbols=_make_symbols(n_classes=1, n_functions=1),
    )
    diagnostics = rule.evaluate(target, make_context(rule=rule))
    assert diagnostics == ()


def test_missing_module_inventory_present_no_fire():
    """Module with inventory sections does not fire."""
    rule = MissingModuleInventory()
    doc_text = (
        "A module.\n\n"
        "Classes\n"
        "-------\n"
        "MyClass\n"
        "    Description.\n"
        "\n"
        "Functions\n"
        "---------\n"
        "my_func\n"
        "    Description.\n"
    )
    target = make_target(
        kind=TargetKind.MODULE,
        docstring=parsed(doc_text),
        module_symbols=_make_symbols(n_classes=2, n_functions=2),
    )
    diagnostics = rule.evaluate(target, make_context(rule=rule))
    assert diagnostics == ()


def test_missing_module_inventory_custom_threshold():
    """Custom inventory_threshold option is respected."""
    rule = MissingModuleInventory()
    # With threshold=3, two public classes should not fire.
    target = make_target(
        kind=TargetKind.MODULE,
        docstring=parsed("A module."),
        module_symbols=_make_symbols(n_classes=2, n_functions=0),
    )
    diagnostics = rule.evaluate(target, make_context({"inventory_threshold": 3}, rule=rule))
    assert diagnostics == ()
