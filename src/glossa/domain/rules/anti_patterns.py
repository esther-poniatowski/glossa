"""Anti-Patterns rules for the glossa docstring linter."""

from __future__ import annotations

from glossa.domain.contracts import (
    ALL_TARGET_KINDS,
    CALLABLE_TARGET_KINDS,
    Diagnostic,
    DocstringEdit,
    EditKind,
    FixPlan,
    LintTarget,
    RuleOptionDescriptor,
    Severity,
    TargetKind,
)
from glossa.domain.models import TypedSectionKind
from glossa.domain.rules import RuleContext, RuleMetadata, make_diagnostic
from glossa.domain.rules._options import validate_string_tuple
from glossa.domain.rules._scanning import scan_rst_directives

_GROUP = "anti-patterns"


# ---------------------------------------------------------------------------
# empty-docstring
# ---------------------------------------------------------------------------


class EmptyDocstring:
    """Fires when a docstring exists but its body is empty or whitespace-only."""

    metadata = RuleMetadata(
        name="empty-docstring",
        group=_GROUP,
        description="Empty docstring body.",
        default_severity=Severity.WARNING,
        applies_to=ALL_TARGET_KINDS,
        fixable=False,
        requires_docstring=False,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        if target.raw_docstring is None:
            return ()

        if target.raw_docstring.body.strip():
            return ()

        return (
            make_diagnostic(
                self, target, context,
                "Docstring body is empty or contains only whitespace.",
            ),
        )


# ---------------------------------------------------------------------------
# trivial-dunder-docstring
# ---------------------------------------------------------------------------

_BOILERPLATE_PHRASES: tuple[str, ...] = (
    "initialize self",
    "return repr",
    "return str",
)


def _is_trivial_summary(summary_text: str, method_name: str) -> bool:
    """Return True if the summary text is considered trivial for a dunder method."""
    text = summary_text.strip()
    if len(text) >= 30:
        return False

    bare_name = method_name.strip("_")
    text_lower = text.lower()

    if bare_name and bare_name in text_lower:
        return True

    for phrase in _BOILERPLATE_PHRASES:
        if text_lower.startswith(phrase):
            return True

    return False


class TrivialDunderDocstring:
    """Fires when a dunder method docstring trivially restates the method name."""

    metadata = RuleMetadata(
        name="trivial-dunder-docstring",
        group=_GROUP,
        description="Trivial dunder method docstring.",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({TargetKind.METHOD}),
        fixable=False,
        option_schema=(
            RuleOptionDescriptor("trivial_dunder_allowlist", (), validate_string_tuple),
        ),
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        method_name = target.ref.symbol_path[-1] if target.ref.symbol_path else ""

        if not (method_name.startswith("__") and method_name.endswith("__")):
            return ()

        allowlist: tuple[str, ...] = context.policy.options["trivial_dunder_allowlist"]  # type: ignore[assignment]
        if method_name in allowlist:
            return ()

        if target.docstring is None:
            return ()
        summary = target.docstring.summary
        if summary is None:
            return ()

        if not _is_trivial_summary(summary.text, method_name):
            return ()

        return (
            make_diagnostic(
                self, target, context,
                f"Docstring for '{method_name}' trivially restates the method name.",
                span=summary.span,
            ),
        )


# ---------------------------------------------------------------------------
# redundant-returns-none
# ---------------------------------------------------------------------------


class RedundantReturnsNone:
    """Fires when a void callable has a Returns section listing only None."""

    metadata = RuleMetadata(
        name="redundant-returns-none",
        group=_GROUP,
        description="Redundant Returns None section for a function that does not return a value.",
        default_severity=Severity.CONVENTION,
        applies_to=CALLABLE_TARGET_KINDS,
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()
        sig = target.signature
        if sig is None:
            return ()

        is_void = (not sig.returns_value) or (sig.return_annotation == "None")
        if not is_void:
            return ()

        section = target.docstring.typed_section(TypedSectionKind.RETURNS)
        if section is None:
            return ()

        has_non_none = any(
            (entry.type_text or "").strip().lower() != "none"
            for entry in section.entries
        )
        if has_non_none:
            return ()

        fix = FixPlan(
            description="Remove redundant 'Returns' section.",
            target=target.ref,
            edits=(
                DocstringEdit(
                    kind=EditKind.DELETE,
                    span=section.span,
                    text="",
                ),
            ),
            affected_rules=("redundant-returns-none",),
        )

        return (
            make_diagnostic(
                self, target, context,
                "Returns section documents 'None' but the callable does not return a value.",
                span=section.span,
                fix=fix,
            ),
        )


# ---------------------------------------------------------------------------
# rst-note-warning-directive
# ---------------------------------------------------------------------------

_RST_NOTE_WARNING_DIRECTIVES = frozenset({"note", "warning"})

_DIRECTIVE_TO_SECTION: dict[str, str] = {
    "note": "Notes",
    "warning": "Warnings",
}


class RstNoteWarningDirective:
    """Fires when prose contains a RST ``.. note::`` or ``.. warning::`` directive."""

    metadata = RuleMetadata(
        name="rst-note-warning-directive",
        group=_GROUP,
        description=(
            "Prose uses a RST note/warning directive; use a NumPy-style section instead."
        ),
        default_severity=Severity.CONVENTION,
        applies_to=ALL_TARGET_KINDS,
        fixable=False,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()
        all_lines = target.docstring.all_text_lines()
        directives = scan_rst_directives(all_lines, _RST_NOTE_WARNING_DIRECTIVES)
        if not directives:
            return ()

        return tuple(
            make_diagnostic(
                self, target, context,
                f"Use a NumPy-style '{_DIRECTIVE_TO_SECTION.get(d, d.capitalize())}' section instead of "
                f"the RST '.. {d}::' directive.",
            )
            for d in directives
        )
