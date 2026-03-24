"""D5xx Anti-Patterns rules for the glossa docstring linter."""

from __future__ import annotations

import re

from glossa.domain.rules import RuleMetadata, RuleContext, scan_rst_directives
from glossa.core.contracts import (
    Diagnostic,
    DocstringEdit,
    EditKind,
    FixPlan,
    LintTarget,
    Severity,
    TargetKind,
)
from glossa.domain.models import TypedSection, TypedSectionKind, ProseSection, ProseSectionKind


# ---------------------------------------------------------------------------
# D500 — Empty docstring body
# ---------------------------------------------------------------------------


class D500:
    """Fires when a docstring exists but its body is empty or whitespace-only."""

    metadata = RuleMetadata(
        code="D500",
        description="Empty docstring body.",
        default_severity=Severity.WARNING,
        applies_to=frozenset({
            TargetKind.MODULE,
            TargetKind.CLASS,
            TargetKind.FUNCTION,
            TargetKind.METHOD,
            TargetKind.PROPERTY,
        }),
        fixable=False,
        requires_docstring=False,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        if target.raw_docstring is None:
            return ()

        if target.raw_docstring.body.strip():
            return ()

        return (
            Diagnostic(
                code=self.metadata.code,
                message="Docstring body is empty or contains only whitespace.",
                severity=context.policy.severity,
                target=target.ref,
                span=None,
                fix=None,
            ),
        )


# ---------------------------------------------------------------------------
# D501 — Trivial dunder method docstring
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

    # Strip surrounding underscores to get the bare name (e.g. "__init__" -> "init")
    bare_name = method_name.strip("_")

    text_lower = text.lower()

    if bare_name and bare_name in text_lower:
        return True

    for phrase in _BOILERPLATE_PHRASES:
        if text_lower.startswith(phrase):
            return True

    return False


class D501:
    """Fires when a dunder method docstring trivially restates the method name."""

    metadata = RuleMetadata(
        code="D501",
        description="Trivial dunder method docstring.",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({TargetKind.METHOD}),
        fixable=False,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        method_name = target.ref.symbol_path[-1] if target.ref.symbol_path else ""

        # Only applies to dunder methods.
        if not (method_name.startswith("__") and method_name.endswith("__")):
            return ()

        # Respect the configured or default allowlist.
        allowlist = context.policy.options.get("trivial_dunder_allowlist", ())
        if method_name in allowlist:
            return ()

        summary = target.docstring.summary
        if summary is None:
            return ()

        if not _is_trivial_summary(summary.text, method_name):
            return ()

        return (
            Diagnostic(
                code=self.metadata.code,
                message=(
                    f"Docstring for '{method_name}' trivially restates the method name."
                ),
                severity=context.policy.severity,
                target=target.ref,
                span=summary.span,
                fix=None,
            ),
        )


# ---------------------------------------------------------------------------
# D502 — Redundant Returns None section
# ---------------------------------------------------------------------------


def _returns_section(target: LintTarget) -> TypedSection | None:
    """Return the Returns TypedSection from a parsed docstring, or None."""
    if target.docstring is None:
        return None
    for section in target.docstring.sections:
        if isinstance(section, TypedSection) and section.kind is TypedSectionKind.RETURNS:
            return section
    return None


def _section_only_none_entries(section: TypedSection) -> bool:
    """Return True when every entry in the section has type_text 'None' (or no entries)."""
    if not section.entries:
        return True
    return all(
        (entry.type_text or "").strip().lower() == "none"
        for entry in section.entries
    )


class D502:
    """Fires when a void callable has a Returns section listing only None."""

    metadata = RuleMetadata(
        code="D502",
        description="Redundant Returns None section for a function that does not return a value.",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({
            TargetKind.FUNCTION,
            TargetKind.METHOD,
            TargetKind.PROPERTY,
        }),
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        sig = target.signature
        if sig is None:
            return ()

        # Check if the callable does not return a value.
        is_void = (not sig.returns_value) or (sig.return_annotation == "None")
        if not is_void:
            return ()

        section = _returns_section(target)
        if section is None:
            return ()

        if not _section_only_none_entries(section):
            return ()

        fix = FixPlan(
            description="Remove redundant 'Returns' section.",
            target=target.ref,
            edits=(
                DocstringEdit(
                    kind=EditKind.DELETE,
                    span=section.span,
                    anchor="",
                    text="",
                ),
            ),
            affected_rules=("D502",),
        )

        return (
            Diagnostic(
                code=self.metadata.code,
                message=(
                    "Returns section documents 'None' but the callable does not return a value."
                ),
                severity=context.policy.severity,
                target=target.ref,
                span=section.span,
                fix=fix,
            ),
        )


# ---------------------------------------------------------------------------
# D503 — Prose uses RST note/warning directive instead of a NumPy section
# ---------------------------------------------------------------------------

_D503_DIRECTIVES = frozenset({"note", "warning"})

_DIRECTIVE_TO_SECTION: dict[str, str] = {
    "note": "Notes",
    "warning": "Warnings",
}


class D503:
    """Fires when prose contains a RST ``.. note::`` or ``.. warning::`` directive."""

    metadata = RuleMetadata(
        code="D503",
        description=(
            "Prose uses a RST note/warning directive; use a NumPy-style section instead."
        ),
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({
            TargetKind.MODULE,
            TargetKind.CLASS,
            TargetKind.FUNCTION,
            TargetKind.METHOD,
            TargetKind.PROPERTY,
        }),
        fixable=False,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        all_lines: list[str] = list(target.docstring.extended_description_lines)
        for section in target.docstring.sections:
            if isinstance(section, ProseSection):
                all_lines.extend(section.body_lines)

        directives = scan_rst_directives(tuple(all_lines), _D503_DIRECTIVES)
        if not directives:
            return ()

        return tuple(
            Diagnostic(
                code=self.metadata.code,
                message=(
                    f"Use a NumPy-style '{_DIRECTIVE_TO_SECTION.get(d, d.capitalize())}' section instead of "
                    f"the RST '.. {d}::' directive."
                ),
                severity=context.policy.severity,
                target=target.ref,
                span=None,
                fix=None,
            )
            for d in directives
        )
