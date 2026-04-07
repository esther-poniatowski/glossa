"""Tests for D2xx prose and summary format rules."""

from __future__ import annotations

from glossa.domain.contracts import (
    AttributeFact,
    ExceptionFact,
    ExtractedTarget,
    LintTarget,
    ModuleSymbolFact,
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
from glossa.domain.rules.prose import (
    D200,
    D201,
    D202,
    D203,
    D204,
    D205,
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


def parsed(text: str):
    """Parse a docstring body into a ParsedDocstring."""
    return parse_docstring(body=text, quote='"""', string_prefix="", indentation="    ")


# ---------------------------------------------------------------------------
# D200 — Imperative voice
# ---------------------------------------------------------------------------


def test_d200_imperative():
    """'Return the value.' uses imperative voice and should not fire."""
    target = make_target(docstring=parsed("Return the value."))
    diagnostics = D200().evaluate(target, make_context())
    assert diagnostics == ()


def test_d200_non_imperative_third_person():
    """'Returns the value.' is third-person and should fire D200."""
    target = make_target(docstring=parsed("Returns the value."))
    diagnostics = D200().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "non-imperative-summary"


def test_d200_non_imperative_gerund():
    """Gerund form (e.g. 'Returning the value.') should fire D200."""
    target = make_target(docstring=parsed("Returning the value."))
    diagnostics = D200().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "non-imperative-summary"




# ---------------------------------------------------------------------------
# D201 — Terminal period
# ---------------------------------------------------------------------------


def test_d201_missing_period():
    """Summary without a trailing period fires D201."""
    target = make_target(docstring=parsed("Do something"))
    diagnostics = D201().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "missing-period"


def test_d201_period_present():
    """Summary with a trailing period does not fire D201."""
    target = make_target(docstring=parsed("Do something."))
    diagnostics = D201().evaluate(target, make_context())
    assert diagnostics == ()


def test_d201_fix_plan():
    """D201 diagnostic includes a fix plan with the corrected text."""
    target = make_target(docstring=parsed("Do something"))
    diagnostics = D201().evaluate(target, make_context())
    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.fix is not None
    assert diag.fix.description != ""
    assert len(diag.fix.edits) == 1
    assert "Do something." in diag.fix.edits[0].text



# ---------------------------------------------------------------------------
# D202 — Blank line after summary
# ---------------------------------------------------------------------------


def test_d202_missing_blank_line():
    """Summary immediately followed by section content (no blank line) fires D202."""
    # No blank line between summary and the Notes section header.
    doc_text = (
        "Do something.\n"
        "Notes\n"
        "-----\n"
        "Some extra detail.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D202().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "missing-blank-after-summary"


def test_d202_blank_line_present():
    """Summary followed by a blank line and body does not fire D202."""
    doc_text = (
        "Do something.\n"
        "\n"
        "Notes\n"
        "-----\n"
        "Some extra detail.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D202().evaluate(target, make_context())
    assert diagnostics == ()


def test_d202_summary_only_no_fire():
    """Docstring with only a summary line does not fire D202."""
    target = make_target(docstring=parsed("Do something."))
    diagnostics = D202().evaluate(target, make_context())
    assert diagnostics == ()



# ---------------------------------------------------------------------------
# D203 — First-person voice
# ---------------------------------------------------------------------------


def test_d203_first_person():
    """'I compute the sum.' uses first-person and fires D203."""
    target = make_target(docstring=parsed("I compute the sum."))
    diagnostics = D203().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "first-person-voice"


def test_d203_third_person_no_fire():
    """Third-person summary does not fire D203."""
    target = make_target(docstring=parsed("Compute the sum."))
    diagnostics = D203().evaluate(target, make_context())
    assert diagnostics == ()


def test_d203_my_fires():
    """'my' is a first-person pronoun and fires D203."""
    target = make_target(docstring=parsed("Store my result."))
    diagnostics = D203().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "first-person-voice"



# ---------------------------------------------------------------------------
# D204 — Second-person voice
# ---------------------------------------------------------------------------


def test_d204_second_person():
    """'You should call this.' uses second-person and fires D204."""
    target = make_target(docstring=parsed("You should call this."))
    diagnostics = D204().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "second-person-voice"


def test_d204_your_fires():
    """'Pass your config.' fires D204."""
    target = make_target(docstring=parsed("Pass your config."))
    diagnostics = D204().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "second-person-voice"


def test_d204_third_person_no_fire():
    """Third-person summary does not fire D204."""
    target = make_target(docstring=parsed("Compute the sum."))
    diagnostics = D204().evaluate(target, make_context())
    assert diagnostics == ()



# ---------------------------------------------------------------------------
# D205 — Markdown syntax
# ---------------------------------------------------------------------------


def test_d205_markdown_heading():
    """A Markdown ATX heading in the docstring fires D205."""
    doc_text = "Do something.\n\n# Heading\n\nSome text.\n"
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D205().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "markdown-in-docstring"


def test_d205_markdown_link():
    """A Markdown inline link in the docstring fires D205."""
    doc_text = "Do something.\n\nSee `[the docs](https://example.com)` for details.\n"
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D205().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "markdown-in-docstring"


def test_d205_markdown_fence():
    """A Markdown fenced code block in the docstring fires D205."""
    doc_text = "Do something.\n\n```python\nprint('hi')\n```\n"
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D205().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "markdown-in-docstring"


def test_d205_rst_is_fine():
    """Normal RST-style markup does not fire D205."""
    doc_text = (
        "Do something.\n\n"
        "Use :func:`foo` or :class:`Bar` for details.\n\n"
        "Notes\n"
        "-----\n"
        "See also ``some_function``.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D205().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# D200 — Class targets
# ---------------------------------------------------------------------------


def test_d200_class_target_not_fired():
    """non-imperative-summary does not fire on CLASS targets (noun phrases are valid).

    The runner skips rules whose ``applies_to`` does not include the target
    kind, so CLASS must not appear in D200's ``applies_to`` set.
    """
    assert TargetKind.CLASS not in D200.metadata.applies_to


# ---------------------------------------------------------------------------
# D203 — Code block filtering
# ---------------------------------------------------------------------------


def test_d203_my_in_code_block_no_fire():
    """'my' inside a code example should not fire D203."""
    doc_text = (
        "Compute the sum.\n\n"
        "Examples\n"
        "--------\n"
        ">>> my_var = compute()\n"
        ">>> print(my_var)\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D203().evaluate(target, make_context())
    assert diagnostics == ()


def test_d203_my_in_rst_code_block_no_fire():
    """'my' inside an RST code-block should not fire D203."""
    doc_text = (
        "Compute the sum.\n\n"
        ".. code-block:: python\n\n"
        "    my_var = compute()\n"
        "    print(my_var)\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D203().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# D202 — reST title header
# ---------------------------------------------------------------------------


def test_d202_rst_title_not_misidentified():
    """A reST title header should not cause a false positive for missing blank line."""
    doc_text = (
        "mymodule.core\n"
        "=============\n\n"
        "Core utilities for the framework.\n\n"
        "Notes\n"
        "-----\n"
        "Some details.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = D202().evaluate(target, make_context())
    assert diagnostics == ()
