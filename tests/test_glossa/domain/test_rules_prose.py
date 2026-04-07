"""Tests for prose and summary format rules."""

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
    FirstPersonVoice,
    MarkdownInDocstring,
    MissingBlankAfterSummary,
    MissingPeriod,
    NonImperativeSummary,
    SecondPersonVoice,
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
# NonImperativeSummary — Imperative voice
# ---------------------------------------------------------------------------


def test_non_imperative_summary_imperative_no_fire():
    """'Return the value.' uses imperative voice and should not fire."""
    target = make_target(docstring=parsed("Return the value."))
    diagnostics = NonImperativeSummary().evaluate(target, make_context())
    assert diagnostics == ()


def test_non_imperative_summary_third_person_fires():
    """'Returns the value.' is third-person and should fire."""
    target = make_target(docstring=parsed("Returns the value."))
    diagnostics = NonImperativeSummary().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "non-imperative-summary"


def test_non_imperative_summary_gerund_fires():
    """Gerund form (e.g. 'Returning the value.') should fire."""
    target = make_target(docstring=parsed("Returning the value."))
    diagnostics = NonImperativeSummary().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "non-imperative-summary"




# ---------------------------------------------------------------------------
# MissingPeriod — Terminal period
# ---------------------------------------------------------------------------


def test_missing_period_fires():
    """Summary without a trailing period fires."""
    target = make_target(docstring=parsed("Do something"))
    diagnostics = MissingPeriod().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "missing-period"


def test_missing_period_present_no_fire():
    """Summary with a trailing period does not fire."""
    target = make_target(docstring=parsed("Do something."))
    diagnostics = MissingPeriod().evaluate(target, make_context())
    assert diagnostics == ()


def test_missing_period_fix_plan():
    """MissingPeriod diagnostic includes a fix plan with the corrected text."""
    target = make_target(docstring=parsed("Do something"))
    diagnostics = MissingPeriod().evaluate(target, make_context())
    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.fix is not None
    assert diag.fix.description != ""
    assert len(diag.fix.edits) == 1
    assert "Do something." in diag.fix.edits[0].text



# ---------------------------------------------------------------------------
# MissingBlankAfterSummary — Blank line after summary
# ---------------------------------------------------------------------------


def test_missing_blank_after_summary_fires():
    """Summary immediately followed by section content (no blank line) fires."""
    # No blank line between summary and the Notes section header.
    doc_text = (
        "Do something.\n"
        "Notes\n"
        "-----\n"
        "Some extra detail.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = MissingBlankAfterSummary().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "missing-blank-after-summary"


def test_missing_blank_after_summary_present_no_fire():
    """Summary followed by a blank line and body does not fire."""
    doc_text = (
        "Do something.\n"
        "\n"
        "Notes\n"
        "-----\n"
        "Some extra detail.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = MissingBlankAfterSummary().evaluate(target, make_context())
    assert diagnostics == ()


def test_missing_blank_after_summary_summary_only_no_fire():
    """Docstring with only a summary line does not fire."""
    target = make_target(docstring=parsed("Do something."))
    diagnostics = MissingBlankAfterSummary().evaluate(target, make_context())
    assert diagnostics == ()



# ---------------------------------------------------------------------------
# FirstPersonVoice — First-person voice
# ---------------------------------------------------------------------------


def test_first_person_voice_fires():
    """'I compute the sum.' uses first-person and fires."""
    target = make_target(docstring=parsed("I compute the sum."))
    diagnostics = FirstPersonVoice().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "first-person-voice"


def test_first_person_voice_third_person_no_fire():
    """Third-person summary does not fire."""
    target = make_target(docstring=parsed("Compute the sum."))
    diagnostics = FirstPersonVoice().evaluate(target, make_context())
    assert diagnostics == ()


def test_first_person_voice_my_fires():
    """'my' is a first-person pronoun and fires."""
    target = make_target(docstring=parsed("Store my result."))
    diagnostics = FirstPersonVoice().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "first-person-voice"



# ---------------------------------------------------------------------------
# SecondPersonVoice — Second-person voice
# ---------------------------------------------------------------------------


def test_second_person_voice_fires():
    """'You should call this.' uses second-person and fires."""
    target = make_target(docstring=parsed("You should call this."))
    diagnostics = SecondPersonVoice().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "second-person-voice"


def test_second_person_voice_your_fires():
    """'Pass your config.' fires."""
    target = make_target(docstring=parsed("Pass your config."))
    diagnostics = SecondPersonVoice().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "second-person-voice"


def test_second_person_voice_third_person_no_fire():
    """Third-person summary does not fire."""
    target = make_target(docstring=parsed("Compute the sum."))
    diagnostics = SecondPersonVoice().evaluate(target, make_context())
    assert diagnostics == ()



# ---------------------------------------------------------------------------
# MarkdownInDocstring — Markdown syntax
# ---------------------------------------------------------------------------


def test_markdown_in_docstring_heading_fires():
    """A Markdown ATX heading in the docstring fires."""
    doc_text = "Do something.\n\n# Heading\n\nSome text.\n"
    target = make_target(docstring=parsed(doc_text))
    diagnostics = MarkdownInDocstring().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "markdown-in-docstring"


def test_markdown_in_docstring_link_fires():
    """A Markdown inline link in the docstring fires."""
    doc_text = "Do something.\n\nSee `[the docs](https://example.com)` for details.\n"
    target = make_target(docstring=parsed(doc_text))
    diagnostics = MarkdownInDocstring().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "markdown-in-docstring"


def test_markdown_in_docstring_fence_fires():
    """A Markdown fenced code block in the docstring fires."""
    doc_text = "Do something.\n\n```python\nprint('hi')\n```\n"
    target = make_target(docstring=parsed(doc_text))
    diagnostics = MarkdownInDocstring().evaluate(target, make_context())
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "markdown-in-docstring"


def test_markdown_in_docstring_rst_no_fire():
    """Normal RST-style markup does not fire."""
    doc_text = (
        "Do something.\n\n"
        "Use :func:`foo` or :class:`Bar` for details.\n\n"
        "Notes\n"
        "-----\n"
        "See also ``some_function``.\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = MarkdownInDocstring().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# NonImperativeSummary — Class targets
# ---------------------------------------------------------------------------


def test_non_imperative_summary_class_target_not_fired():
    """non-imperative-summary does not fire on CLASS targets (noun phrases are valid).

    The runner skips rules whose ``applies_to`` does not include the target
    kind, so CLASS must not appear in NonImperativeSummary's ``applies_to`` set.
    """
    assert TargetKind.CLASS not in NonImperativeSummary.metadata.applies_to


# ---------------------------------------------------------------------------
# FirstPersonVoice — Code block filtering
# ---------------------------------------------------------------------------


def test_first_person_voice_my_in_code_block_no_fire():
    """'my' inside a code example should not fire."""
    doc_text = (
        "Compute the sum.\n\n"
        "Examples\n"
        "--------\n"
        ">>> my_var = compute()\n"
        ">>> print(my_var)\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = FirstPersonVoice().evaluate(target, make_context())
    assert diagnostics == ()


def test_first_person_voice_my_in_rst_code_block_no_fire():
    """'my' inside an RST code-block should not fire."""
    doc_text = (
        "Compute the sum.\n\n"
        ".. code-block:: python\n\n"
        "    my_var = compute()\n"
        "    print(my_var)\n"
    )
    target = make_target(docstring=parsed(doc_text))
    diagnostics = FirstPersonVoice().evaluate(target, make_context())
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# MissingBlankAfterSummary — reST title header
# ---------------------------------------------------------------------------


def test_missing_blank_after_summary_rst_title_not_misidentified():
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
    diagnostics = MissingBlankAfterSummary().evaluate(target, make_context())
    assert diagnostics == ()
