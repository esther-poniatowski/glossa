"""Prose and Summary Format rules."""

from __future__ import annotations

import re

from glossa.domain.contracts import (
    ALL_TARGET_KINDS,
    CALLABLE_TARGET_KINDS,
    Diagnostic,
    DocstringEdit,
    EditKind,
    FixPlan,
    LintTarget,
    Severity,
)
from glossa.domain.rules import RuleContext, RuleMetadata, make_diagnostic

_GROUP = "prose"


# ---------------------------------------------------------------------------
# non-imperative-summary
# ---------------------------------------------------------------------------


def _is_non_imperative(summary_text: str) -> bool:
    """Return True when the summary appears to open with a non-imperative verb."""
    if not summary_text:
        return False

    first_word_match = re.match(r"^([A-Za-z]+)", summary_text)
    if not first_word_match:
        return False

    first_word = first_word_match.group(1)
    lower = first_word.lower()

    if lower.endswith("ing"):
        return True

    if (
        lower.endswith("s")
        and not lower.endswith("ss")
        and not lower.endswith("us")
        and not lower.endswith("is")
        and re.match(r"^[A-Za-z]+s\s", summary_text)
    ):
        return True

    return False


class NonImperativeSummary:
    """Summary line is not imperative where imperative voice is required."""

    metadata = RuleMetadata(
        name="non-imperative-summary",
        group=_GROUP,
        description="Summary line is not imperative where imperative voice is required.",
        default_severity=Severity.CONVENTION,
        applies_to=CALLABLE_TARGET_KINDS,
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()
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
# missing-period
# ---------------------------------------------------------------------------


class MissingPeriod:
    """Summary line missing terminal period."""

    metadata = RuleMetadata(
        name="missing-period",
        group=_GROUP,
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
        if target.docstring is None:
            return ()
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
                    text=fixed_text,
                ),
            ),
            affected_rules=("missing-period",),
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
# missing-blank-after-summary
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


class MissingBlankAfterSummary:
    """Missing blank line after summary when body follows."""

    metadata = RuleMetadata(
        name="missing-blank-after-summary",
        group=_GROUP,
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
        if target.docstring is None:
            return ()
        parsed = target.docstring
        summary = parsed.summary

        if summary is None:
            return ()

        has_body = bool(parsed.extended_description_lines or parsed.sections)
        if not has_body:
            return ()

        # Check for blank line after summary using the summary span end offset.
        raw_body = parsed.syntax.raw_body
        end = summary.span.end_offset
        remaining = raw_body[end:]
        # The next non-whitespace-on-line character after the summary should be
        # preceded by at least one blank line.
        lines_after = remaining.split("\n")
        if len(lines_after) >= 2 and not lines_after[1].strip():
            return ()

        return (
            make_diagnostic(
                self, target, context,
                "Missing blank line between summary and body.",
                span=summary.span,
            ),
        )


# ---------------------------------------------------------------------------
# first-person-voice
# ---------------------------------------------------------------------------

_CODE_LINE_RE = re.compile(r"^\s*(>>>|\.\.\.)\s")
_RST_CODE_BLOCK_RE = re.compile(r"^\s*\.\.\s+(code-block|code|sourcecode)::")


def _filter_code_lines(lines: tuple[str, ...]) -> str:
    """Join text lines, excluding code examples.

    Filters out interactive prompts (>>>), RST code-block directives, and
    their indented continuation lines.
    """
    result: list[str] = []
    in_code_block = False
    code_block_indent: int | None = None
    for line in lines:
        # Interactive Python prompts
        if _CODE_LINE_RE.match(line):
            in_code_block = True
            code_block_indent = None
            continue
        # RST code-block directives
        if _RST_CODE_BLOCK_RE.match(line):
            in_code_block = True
            code_block_indent = len(line) - len(line.lstrip())
            continue
        if in_code_block:
            if line.strip() == "":
                continue
            line_indent = len(line) - len(line.lstrip())
            if code_block_indent is not None and line_indent > code_block_indent:
                continue
            if code_block_indent is None and line.startswith("    "):
                continue
            in_code_block = False
        result.append(line)
    return "\n".join(result)


_FIRST_PERSON_RE = re.compile(r"\b(I(?!/)|my|me|we|our|us)\b")


class FirstPersonVoice:
    """First-person voice in docstring."""

    metadata = RuleMetadata(
        name="first-person-voice",
        group=_GROUP,
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
        if target.docstring is None:
            return ()
        text = _filter_code_lines(target.docstring.all_text_lines())
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
# second-person-voice
# ---------------------------------------------------------------------------

_SECOND_PERSON_RE = re.compile(r"\b(you|your|yours)\b", re.IGNORECASE)


class SecondPersonVoice:
    """Second-person voice in docstring."""

    metadata = RuleMetadata(
        name="second-person-voice",
        group=_GROUP,
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
        if target.docstring is None:
            return ()
        text = _filter_code_lines(target.docstring.all_text_lines())
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
# markdown-in-docstring
# ---------------------------------------------------------------------------

_MD_HEADING_RE = re.compile(r"^#{1,6} ", re.MULTILINE)
_MD_FENCE_RE = re.compile(r"```")
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


class MarkdownInDocstring:
    """Markdown syntax where RST is required."""

    metadata = RuleMetadata(
        name="markdown-in-docstring",
        group=_GROUP,
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
        if target.docstring is None:
            return ()
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
