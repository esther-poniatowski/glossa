"""D2xx — Prose and Summary Format rules."""

from __future__ import annotations

import re

from glossa.core.contracts import (
    ALL_TARGET_KINDS,
    NON_PROPERTY_KINDS,
    DocstringEdit,
    EditKind,
    FixPlan,
    LintTarget,
    Severity,
)
from glossa.domain.rules import RuleContext, RuleMetadata, make_diagnostic


# ---------------------------------------------------------------------------
# D200 — Summary line is not imperative where imperative voice is required
# ---------------------------------------------------------------------------


def _is_non_imperative(summary_text: str) -> bool:
    """Return True when the summary appears to open with a non-imperative verb.

    The heuristic targets the most common offenders:
    - Third-person singular present tense: the first word ends in a single
      's' that is *not* part of an 'ss', 'us', or 'is' suffix and is
      followed by whitespace (e.g. "Returns the value").
    - Common gerund forms: the first word ends in 'ing' (e.g. "Getting",
      "Returning", "Setting").
    """
    if not summary_text:
        return False

    first_word_match = re.match(r"^([A-Za-z]+)", summary_text)
    if not first_word_match:
        return False

    first_word = first_word_match.group(1)
    lower = first_word.lower()

    # Gerund: ends in 'ing'
    if lower.endswith("ing"):
        return True

    # Third-person singular: ends in a single 's' not preceded by another 's',
    # 'u', or 'i' (avoids words like "process", "focus", "basis", "this").
    # Also require that a space follows (so we don't fire on single-word summaries).
    if (
        lower.endswith("s")
        and not lower.endswith("ss")
        and not lower.endswith("us")
        and not lower.endswith("is")
        and re.match(r"^[A-Za-z]+s\s", summary_text)
    ):
        return True

    return False


class D200:
    """Summary line is not imperative where imperative voice is required."""

    metadata = RuleMetadata(
        code="D200",
        description="Summary line is not imperative where imperative voice is required.",
        default_severity=Severity.CONVENTION,
        applies_to=NON_PROPERTY_KINDS,
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        summary = target.docstring.summary
        if summary is None:
            return ()

        if not _is_non_imperative(summary.text):
            return ()

        return (
            make_diagnostic(
                self, target, context,
                f'Summary line should use imperative voice '
                f'(e.g. "Return \u2026" not "{summary.text.split()[0]} \u2026").',
                span=summary.span,
            ),
        )


# ---------------------------------------------------------------------------
# D201 — Summary line missing terminal period
# ---------------------------------------------------------------------------


class D201:
    """Summary line missing terminal period."""

    metadata = RuleMetadata(
        code="D201",
        description="Summary line missing terminal period.",
        default_severity=Severity.CONVENTION,
        applies_to=ALL_TARGET_KINDS,
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        summary = target.docstring.summary
        if summary is None:
            return ()

        if summary.text.endswith("."):
            return ()

        fixed_text = summary.text + "."
        fix = FixPlan(
            description="Append a period to the summary line.",
            target=target.ref,
            edits=(
                DocstringEdit(
                    kind=EditKind.REPLACE,
                    span=summary.span,
                    anchor="",
                    text=fixed_text,
                ),
            ),
            affected_rules=("D201",),
        )

        return (
            make_diagnostic(
                self, target, context,
                "Summary line is missing a terminal period.",
                span=summary.span,
                fix=fix,
            ),
        )


# ---------------------------------------------------------------------------
# D202 — Missing blank line after summary when body follows
# ---------------------------------------------------------------------------


def _has_blank_line_after_summary(raw_body: str) -> bool:
    """Return True when the raw docstring body has a blank line after the summary."""
    lines = raw_body.splitlines()
    summary_line_index: int | None = None

    for i, line in enumerate(lines):
        if line.strip():
            summary_line_index = i
            break

    if summary_line_index is None:
        return True

    next_index = summary_line_index + 1
    if next_index >= len(lines):
        return True

    return not lines[next_index].strip()


class D202:
    """Missing blank line after summary when body follows."""

    metadata = RuleMetadata(
        code="D202",
        description="Missing blank line after summary when body follows.",
        default_severity=Severity.CONVENTION,
        applies_to=ALL_TARGET_KINDS,
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        parsed = target.docstring
        summary = parsed.summary

        if summary is None:
            return ()

        has_body = bool(parsed.extended_description_lines or parsed.sections)
        if not has_body:
            return ()

        raw_body = parsed.syntax.raw_body
        if _has_blank_line_after_summary(raw_body):
            return ()

        return (
            make_diagnostic(
                self, target, context,
                "Missing blank line between summary and body.",
                span=summary.span,
            ),
        )


# ---------------------------------------------------------------------------
# D203 — First-person voice in docstring
# ---------------------------------------------------------------------------

_FIRST_PERSON_RE = re.compile(r"\b(I|my|me|we|our|us)\b")


class D203:
    """First-person voice in docstring."""

    metadata = RuleMetadata(
        code="D203",
        description="First-person voice in docstring.",
        default_severity=Severity.WARNING,
        applies_to=ALL_TARGET_KINDS,
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        text = "\n".join(target.docstring.all_text_lines())
        match = _FIRST_PERSON_RE.search(text)
        if match is None:
            return ()

        return (
            make_diagnostic(
                self, target, context,
                f'Avoid first-person voice in docstrings (found "{match.group()}").',
            ),
        )


# ---------------------------------------------------------------------------
# D204 — Second-person voice in docstring
# ---------------------------------------------------------------------------

_SECOND_PERSON_RE = re.compile(r"\b(you|your|yours)\b", re.IGNORECASE)


class D204:
    """Second-person voice in docstring."""

    metadata = RuleMetadata(
        code="D204",
        description="Second-person voice in docstring.",
        default_severity=Severity.WARNING,
        applies_to=ALL_TARGET_KINDS,
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        text = "\n".join(target.docstring.all_text_lines())
        match = _SECOND_PERSON_RE.search(text)
        if match is None:
            return ()

        return (
            make_diagnostic(
                self, target, context,
                f'Avoid second-person voice in docstrings (found "{match.group()}").',
            ),
        )


# ---------------------------------------------------------------------------
# D205 — Markdown syntax where RST is required
# ---------------------------------------------------------------------------

# Matches a Markdown ATX heading: a line that starts with one or more '#'
# followed by a space.
_MD_HEADING_RE = re.compile(r"^#{1,6} ", re.MULTILINE)

# Matches a fenced code block delimiter (triple backtick).
_MD_FENCE_RE = re.compile(r"```")

# Matches a Markdown inline link: [text](url).  We require a non-empty label
# and a non-empty URL to avoid false positives on RST cross-references.
_MD_LINK_RE = re.compile(r"\[.+?\]\(.+?\)")


def _detect_markdown(text: str) -> str | None:
    """Return a short description of the first Markdown pattern found, or None."""
    if _MD_HEADING_RE.search(text):
        return "Markdown heading (`# \u2026`)"
    if _MD_FENCE_RE.search(text):
        return "Markdown fenced code block (` ``` `)"
    if _MD_LINK_RE.search(text):
        return "Markdown link (`[text](url)`)"
    return None


class D205:
    """Markdown syntax where RST is required."""

    metadata = RuleMetadata(
        code="D205",
        description="Markdown syntax where RST is required.",
        default_severity=Severity.WARNING,
        applies_to=ALL_TARGET_KINDS,
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        raw_body = target.docstring.syntax.raw_body
        found = _detect_markdown(raw_body)
        if found is None:
            return ()

        return (
            make_diagnostic(
                self, target, context,
                f"Markdown syntax detected in docstring: {found}. Use RST instead.",
            ),
        )
