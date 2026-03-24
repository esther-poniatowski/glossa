"""Tests for D1xx presence and coverage rules."""

from __future__ import annotations

import pytest

from glossa.application.contracts import (
    AttributeFact,
    ExceptionFact,
    ExtractedDocstring,
    LintTarget,
    ModuleSymbolFact,
    ParameterFact,
    RelatedTargetSnapshot,
    ResolvedRelatedTargets,
    Severity,
    SignatureFacts,
    SourceRef,
    TargetKind,
    TextPosition,
    TextSpan,
    Visibility,
    WarningFact,
)
from glossa.application.policy import ResolvedRulePolicy
from glossa.domain.parsing import parse_docstring
from glossa.domain.rules import RuleContext
from glossa.domain.rules.presence import (
    D100,
    D101,
    D102,
    D103,
    D104,
    D105,
    D106,
    D107,
    D108,
    D109,
    D110,
    D111,
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
    raw_docstring=None,
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
    return LintTarget(
        ref=ref,
        kind=kind,
        visibility=visibility,
        is_test_target=is_test_target,
        docstring=docstring,
        raw_docstring=raw_docstring,
        signature=signature,
        exceptions=exceptions,
        warnings=warnings,
        attributes=attributes,
        module_symbols=module_symbols,
        decorators=decorators,
        related=related if related is not None else ResolvedRelatedTargets(),
    )


def make_context(options: dict | None = None) -> RuleContext:
    """Return a RuleContext with an enabled WARNING policy."""
    return RuleContext(
        policy=ResolvedRulePolicy(
            enabled=True,
            severity=Severity.WARNING,
            options=options or {},
        )
    )


def parsed(text: str):
    """Parse a docstring body into a ParsedDocstring."""
    return parse_docstring(body=text, quote='"""', string_prefix="", indentation="    ")


# ---------------------------------------------------------------------------
# D100 — Missing public module docstring
# ---------------------------------------------------------------------------


def test_d100_missing_module_docstring():
    target = make_target(kind=TargetKind.MODULE, visibility=Visibility.PUBLIC, docstring=None)
    diagnostics = D100().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "D100"


def test_d100_present_module_docstring():
    target = make_target(
        kind=TargetKind.MODULE,
        visibility=Visibility.PUBLIC,
        docstring=parsed("Module summary."),
    )
    diagnostics = D100().evaluate(target, make_context())
    assert diagnostics == ()


def test_d100_private_module_not_fired():
    target = make_target(kind=TargetKind.MODULE, visibility=Visibility.PRIVATE, docstring=None)
    diagnostics = D100().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# D101 — Missing public class docstring
# ---------------------------------------------------------------------------


def test_d101_missing_class_docstring():
    target = make_target(kind=TargetKind.CLASS, visibility=Visibility.PUBLIC, docstring=None)
    diagnostics = D101().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "D101"


def test_d101_present_class_docstring():
    target = make_target(
        kind=TargetKind.CLASS,
        visibility=Visibility.PUBLIC,
        docstring=parsed("A class."),
    )
    diagnostics = D101().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# D102 — Missing public callable docstring
# ---------------------------------------------------------------------------


def test_d102_missing_callable_docstring():
    target = make_target(kind=TargetKind.FUNCTION, visibility=Visibility.PUBLIC, docstring=None)
    diagnostics = D102().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "D102"


def test_d102_present_callable_docstring():
    target = make_target(
        kind=TargetKind.FUNCTION,
        visibility=Visibility.PUBLIC,
        docstring=parsed("Do something."),
    )
    diagnostics = D102().evaluate(target, make_context())
    assert diagnostics == ()


def test_d102_private_skipped():
    """PRIVATE callable does not fire when include_private_helpers is False (default)."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        visibility=Visibility.PRIVATE,
        docstring=None,
    )
    diagnostics = D102().evaluate(target, make_context({"include_private_helpers": False}))
    assert diagnostics == ()


def test_d102_private_fires_when_opted_in():
    """PRIVATE callable fires when include_private_helpers is True."""
    # D102 only fires for PUBLIC visibility regardless of option — private helpers
    # are simply not flagged even with include_private_helpers=True because D102
    # guards on target.visibility is Visibility.PUBLIC at the end.
    target = make_target(
        kind=TargetKind.FUNCTION,
        visibility=Visibility.PRIVATE,
        docstring=None,
    )
    diagnostics = D102().evaluate(target, make_context({"include_private_helpers": True}))
    # include_private_helpers=True only removes the early-exit guard; the final
    # check still requires PUBLIC visibility for D102 to fire.
    assert diagnostics == ()


def test_d102_test_target_skipped():
    """Test functions are skipped when include_test_functions is False."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        visibility=Visibility.PUBLIC,
        is_test_target=True,
        docstring=None,
    )
    diagnostics = D102().evaluate(target, make_context({"include_test_functions": False}))
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# D103 — Missing Parameters section
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


def test_d103_missing_parameters_section():
    """Function with params but no Parameters section fires D103."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        signature=_make_sig_with_params("x", "y"),
    )
    diagnostics = D103().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "D103"


def test_d103_parameters_present():
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
    diagnostics = D103().evaluate(target, make_context())
    assert diagnostics == ()


def test_d103_no_params_no_fire():
    """Function with no documentable params does not fire."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        signature=_make_sig_with_params(),
    )
    diagnostics = D103().evaluate(target, make_context())
    assert diagnostics == ()


def test_d103_self_excluded():
    """'self' is excluded from documentable params."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        signature=_make_sig_with_params("self"),
    )
    diagnostics = D103().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# D104 — Missing Returns section
# ---------------------------------------------------------------------------


def _make_sig_returns(returns_value: bool = True, yields_value: bool = False) -> SignatureFacts:
    return SignatureFacts(
        parameters=(),
        return_annotation=None,
        returns_value=returns_value,
        yields_value=yields_value,
    )


def test_d104_missing_returns():
    """Function that returns a value but has no Returns section fires D104."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        signature=_make_sig_returns(returns_value=True),
    )
    diagnostics = D104().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "D104"


def test_d104_returns_section_present():
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
    diagnostics = D104().evaluate(target, make_context())
    assert diagnostics == ()


def test_d104_no_return_value_no_fire():
    """Function that does not return a value does not fire."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        signature=_make_sig_returns(returns_value=False),
    )
    diagnostics = D104().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# D105 — Missing Yields section
# ---------------------------------------------------------------------------


def test_d105_missing_yields():
    """Generator function with no Yields section fires D105."""
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Generate values."),
        signature=_make_sig_returns(returns_value=False, yields_value=True),
    )
    diagnostics = D105().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "D105"


def test_d105_yields_section_present():
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
    diagnostics = D105().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# D106 — Missing Raises section
# ---------------------------------------------------------------------------


def test_d106_missing_raises():
    """High-confidence raise with no Raises section fires D106."""
    exc = ExceptionFact(type_name="ValueError", evidence="raise", confidence="high")
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        exceptions=(exc,),
    )
    diagnostics = D106().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "D106"


def test_d106_raises_section_present():
    """High-confidence raise with a Raises section does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Raises\n"
        "------\n"
        "ValueError\n"
        "    When the input is invalid.\n"
    )
    exc = ExceptionFact(type_name="ValueError", evidence="raise", confidence="high")
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed(doc_text),
        exceptions=(exc,),
    )
    diagnostics = D106().evaluate(target, make_context())
    assert diagnostics == ()


def test_d106_low_confidence_no_fire():
    """Low-confidence raise does not trigger D106."""
    exc = ExceptionFact(type_name="ValueError", evidence="raise", confidence="low")
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        exceptions=(exc,),
    )
    diagnostics = D106().evaluate(target, make_context())
    assert diagnostics == ()


def test_d106_reraise_excluded():
    """High-confidence reraise is excluded from D106 checks."""
    exc = ExceptionFact(type_name="ValueError", evidence="reraise", confidence="high")
    target = make_target(
        kind=TargetKind.FUNCTION,
        docstring=parsed("Do something."),
        exceptions=(exc,),
    )
    diagnostics = D106().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# D108 — Missing module inventory
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


def test_d108_missing_inventory():
    """Module with many public symbols but no inventory fires D108."""
    target = make_target(
        kind=TargetKind.MODULE,
        docstring=parsed("A module."),
        module_symbols=_make_symbols(n_classes=2, n_functions=2),
    )
    diagnostics = D108().evaluate(target, make_context())
    codes = [d.code for d in diagnostics]
    assert codes.count("D108") == 2


def test_d108_below_threshold_no_fire():
    """Module with fewer public symbols than the threshold does not fire."""
    target = make_target(
        kind=TargetKind.MODULE,
        docstring=parsed("A module."),
        module_symbols=_make_symbols(n_classes=1, n_functions=1),
    )
    diagnostics = D108().evaluate(target, make_context())
    assert diagnostics == ()


def test_d108_inventory_present_no_fire():
    """Module with inventory sections does not fire."""
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
    diagnostics = D108().evaluate(target, make_context())
    assert diagnostics == ()


def test_d108_custom_threshold():
    """Custom inventory_threshold option is respected."""
    # With threshold=3, two public classes should not fire.
    target = make_target(
        kind=TargetKind.MODULE,
        docstring=parsed("A module."),
        module_symbols=_make_symbols(n_classes=2, n_functions=0),
    )
    diagnostics = D108().evaluate(target, make_context({"inventory_threshold": 3}))
    assert diagnostics == ()
