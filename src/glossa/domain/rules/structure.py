"""D3xx — Section Structure and Placement rules for glossa."""

from __future__ import annotations

import fnmatch
import re

from glossa.core.contracts import Diagnostic, LintTarget, Severity, TargetKind
from glossa.domain.models import (
    InventorySection,
    ProseSection,
    ProseSectionKind,
    SectionNode,
    SeeAlsoSection,
    TypedSection,
    TypedSectionKind,
    UnknownSection,
)
from glossa.domain.rules import RuleContext, RuleMetadata

# ---------------------------------------------------------------------------
# Canonical NumPy section order helpers
# ---------------------------------------------------------------------------

_CANONICAL_ORDER: dict[object, int] = {
    TypedSectionKind.PARAMETERS: 0,
    TypedSectionKind.RETURNS: 1,
    TypedSectionKind.YIELDS: 2,
    TypedSectionKind.RAISES: 3,
    TypedSectionKind.WARNS: 4,
    TypedSectionKind.ATTRIBUTES: 5,
    ProseSectionKind.NOTES: 6,
    ProseSectionKind.WARNINGS: 7,
    # SeeAlsoSection has no kind enum; use a sentinel string key
    "SeeAlso": 8,
    ProseSectionKind.EXAMPLES: 9,
    # InventorySection kinds
    "Classes": 10,
    "Functions": 11,
}


def _canonical_order(section: SectionNode) -> int | None:
    """Return the canonical position index for *section*, or None if unknown."""
    if isinstance(section, TypedSection):
        return _CANONICAL_ORDER.get(section.kind)
    if isinstance(section, ProseSection):
        return _CANONICAL_ORDER.get(section.kind)
    if isinstance(section, SeeAlsoSection):
        return _CANONICAL_ORDER.get("SeeAlso")
    if isinstance(section, InventorySection):
        # Use the string value of InventorySectionKind (e.g. "Classes")
        return _CANONICAL_ORDER.get(section.kind.value)
    # UnknownSection — no canonical position
    return None


# ---------------------------------------------------------------------------
# D300 — Section underline is malformed
# ---------------------------------------------------------------------------

_APPLIES_ALL = frozenset(
    {
        TargetKind.MODULE,
        TargetKind.CLASS,
        TargetKind.FUNCTION,
        TargetKind.METHOD,
        TargetKind.PROPERTY,
    }
)


def _section_title(section: SectionNode) -> str:
    """Return the display title of *section*."""
    if isinstance(section, TypedSection):
        return section.kind.value
    if isinstance(section, ProseSection):
        return section.kind.value
    if isinstance(section, SeeAlsoSection):
        return "See Also"
    if isinstance(section, InventorySection):
        return section.kind.value
    if isinstance(section, UnknownSection):
        return section.title
    return ""  # pragma: no cover


class D300:
    """Section underline is malformed."""

    metadata = RuleMetadata(
        code="D300",
        description="Section underline is malformed",
        default_severity=Severity.WARNING,
        applies_to=_APPLIES_ALL,
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        docstring = target.docstring
        raw_body = docstring.syntax.raw_body
        diagnostics: list[Diagnostic] = []

        for section in docstring.sections:
            # UnknownSection does not have an underline_span
            if isinstance(section, UnknownSection):
                continue

            title = _section_title(section)
            expected_len = len(title)

            ul_span = section.underline_span
            underline_text = raw_body[ul_span.start_offset : ul_span.end_offset]
            # Strip surrounding whitespace/newlines to isolate dashes
            underline_stripped = underline_text.strip()

            malformed = (
                not underline_stripped
                or not re.fullmatch(r"-+", underline_stripped)
                or len(underline_stripped) != expected_len
            )

            if malformed:
                diagnostics.append(
                    Diagnostic(
                        code="D300",
                        message=(
                            f"Section '{title}' has a malformed underline: "
                            f"expected {expected_len} dashes, "
                            f"got {underline_stripped!r}"
                        ),
                        severity=context.policy.severity,
                        target=target.ref,
                        span=ul_span,
                        fix=None,
                    )
                )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# D301 — Section order violates NumPy policy
# ---------------------------------------------------------------------------


class D301:
    """Section order violates NumPy policy."""

    metadata = RuleMetadata(
        code="D301",
        description="Section order violates NumPy policy",
        default_severity=Severity.CONVENTION,
        applies_to=_APPLIES_ALL,
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        sections = target.docstring.sections
        if not sections:
            return ()

        # Collect canonical indices for sections that have a known position.
        ordered: list[tuple[int, SectionNode]] = []
        for section in sections:
            idx = _canonical_order(section)
            if idx is not None:
                ordered.append((idx, section))

        # Check that canonical indices are non-decreasing.
        diagnostics: list[Diagnostic] = []
        prev_idx = -1
        for idx, section in ordered:
            if idx < prev_idx:
                title = _section_title(section)
                diagnostics.append(
                    Diagnostic(
                        code="D301",
                        message=(
                            f"Section '{title}' appears out of canonical NumPy order"
                        ),
                        severity=context.policy.severity,
                        target=target.ref,
                        span=section.span,
                        fix=None,
                    )
                )
            else:
                prev_idx = idx

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# D302 — Undocumented parameter present in signature
# ---------------------------------------------------------------------------

_APPLIES_CALLABLE = frozenset(
    {TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.CLASS}
)

_EXCLUDED_PARAM_NAMES = frozenset({"self", "cls"})


def _docstring_param_names(target: LintTarget) -> frozenset[str]:
    """Return parameter names listed in the Parameters section of *target*."""
    if target.docstring is None:
        return frozenset()
    for section in target.docstring.sections:
        if isinstance(section, TypedSection) and section.kind is TypedSectionKind.PARAMETERS:
            return frozenset(
                entry.name
                for entry in section.entries
                if entry.name is not None
            )
    return frozenset()


def _signature_param_names(target: LintTarget) -> frozenset[str]:
    """Return documentable parameter names from the target signature."""
    if target.signature is None:
        return frozenset()
    return frozenset(
        p.name
        for p in target.signature.parameters
        if p.name not in _EXCLUDED_PARAM_NAMES
    )


def _constructor_param_names(target: LintTarget) -> frozenset[str]:
    """Return parameter names from the related constructor snapshot."""
    constructor = target.related.get("constructor")
    if constructor is None or constructor.signature is None:
        return frozenset()
    return frozenset(
        p.name
        for p in constructor.signature.parameters
        if p.name not in _EXCLUDED_PARAM_NAMES
    )


class D302:
    """Undocumented parameter present in signature."""

    metadata = RuleMetadata(
        code="D302",
        description="Undocumented parameter present in signature",
        default_severity=Severity.WARNING,
        applies_to=_APPLIES_CALLABLE,
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        sig_names = _signature_param_names(target)
        if target.kind is TargetKind.CLASS:
            sig_names = sig_names | _constructor_param_names(target)

        doc_names = _docstring_param_names(target)
        missing = sig_names - doc_names

        diagnostics: list[Diagnostic] = []
        for name in sorted(missing):
            diagnostics.append(
                Diagnostic(
                    code="D302",
                    message=f"Parameter '{name}' is in the signature but missing from the docstring",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                    fix=None,
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# D303 — Extraneous parameter appears in docstring
# ---------------------------------------------------------------------------


class D303:
    """Extraneous parameter appears in docstring."""

    metadata = RuleMetadata(
        code="D303",
        description="Extraneous parameter appears in docstring",
        default_severity=Severity.WARNING,
        applies_to=_APPLIES_CALLABLE,
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        sig_names = _signature_param_names(target)
        if target.kind is TargetKind.CLASS:
            sig_names = sig_names | _constructor_param_names(target)

        doc_names = _docstring_param_names(target)
        extra = doc_names - sig_names

        diagnostics: list[Diagnostic] = []
        for name in sorted(extra):
            diagnostics.append(
                Diagnostic(
                    code="D303",
                    message=f"Parameter '{name}' appears in the docstring but not in the signature",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                    fix=None,
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# D304 — Deprecation directive is malformed or misplaced
# ---------------------------------------------------------------------------


class D304:
    """Deprecation directive is malformed or misplaced."""

    metadata = RuleMetadata(
        code="D304",
        description="Deprecation directive is malformed or misplaced",
        default_severity=Severity.WARNING,
        applies_to=_APPLIES_ALL,
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        deprecation = target.docstring.deprecation
        if deprecation is None:
            return ()

        diagnostics: list[Diagnostic] = []

        # Check 1: version must be present.
        if deprecation.version is None:
            diagnostics.append(
                Diagnostic(
                    code="D304",
                    message="Deprecation directive is missing a version",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=deprecation.span,
                    fix=None,
                )
            )

        # Check 2: deprecation must appear before any sections and with a
        # minimal extended description (i.e. it should be close to the top).
        # The parser places the deprecation directive as a separate field;
        # misplacement is indicated by sections or a non-empty
        # extended_description appearing before it.  We approximate
        # "misplaced" as: there are sections AND the extended description has
        # content, suggesting the deprecation was buried after prose.
        has_sections = len(target.docstring.sections) > 0
        extended_non_empty = any(
            line.strip()
            for line in target.docstring.extended_description_lines
        )
        if has_sections and extended_non_empty:
            diagnostics.append(
                Diagnostic(
                    code="D304",
                    message=(
                        "Deprecation directive should appear immediately after the "
                        "summary, before the extended description and sections"
                    ),
                    severity=context.policy.severity,
                    target=target.ref,
                    span=deprecation.span,
                    fix=None,
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# D305 — RST directive used where a NumPy section exists
# ---------------------------------------------------------------------------

_RST_DIRECTIVE_PATTERN = re.compile(
    r"^\s*\.\.\s+"
    r"(note|warning|seealso|see-also|admonition|attention|caution|danger|error|hint|important|tip)"
    r"\s*::",
    re.IGNORECASE,
)


def _section_body_lines(section: SectionNode) -> tuple[str, ...]:
    """Return body/prose lines from any section type."""
    if isinstance(section, TypedSection):
        lines: list[str] = []
        for entry in section.entries:
            lines.extend(entry.description_lines)
        return tuple(lines)
    if isinstance(section, ProseSection):
        return section.body_lines
    if isinstance(section, InventorySection):
        lines = []
        for item in section.items:
            lines.extend(item.description_lines)
        return tuple(lines)
    if isinstance(section, SeeAlsoSection):
        lines = []
        for item in section.items:
            lines.extend(item.description_lines)
        return tuple(lines)
    if isinstance(section, UnknownSection):
        return section.body_lines
    return ()  # pragma: no cover


class D305:
    """RST directive used where a NumPy section exists."""

    metadata = RuleMetadata(
        code="D305",
        description="RST directive used where a NumPy section exists",
        default_severity=Severity.WARNING,
        applies_to=_APPLIES_ALL,
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        diagnostics: list[Diagnostic] = []

        def _check_lines(lines: tuple[str, ...]) -> None:
            for line in lines:
                if _RST_DIRECTIVE_PATTERN.match(line):
                    diagnostics.append(
                        Diagnostic(
                            code="D305",
                            message=(
                                "RST directive found where a NumPy section should be used: "
                                f"{line.strip()!r}"
                            ),
                            severity=context.policy.severity,
                            target=target.ref,
                            span=None,
                            fix=None,
                        )
                    )

        # Check extended description
        _check_lines(target.docstring.extended_description_lines)

        # Check each section's body
        for section in target.docstring.sections:
            _check_lines(_section_body_lines(section))

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# D306 — Examples appears in a non-entry-point module docstring
# ---------------------------------------------------------------------------


class D306:
    """Examples appears in a non-entry-point module docstring."""

    metadata = RuleMetadata(
        code="D306",
        description="Examples appears in a non-entry-point module docstring",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({TargetKind.MODULE}),
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        # Check whether this module is an API entry point.
        source_id = target.ref.source_id
        for pattern in context.policy.options.api_entry_modules:
            if fnmatch.fnmatch(source_id, pattern):
                return ()

        # Look for an Examples section.
        diagnostics: list[Diagnostic] = []
        for section in target.docstring.sections:
            if (
                isinstance(section, ProseSection)
                and section.kind is ProseSectionKind.EXAMPLES
            ):
                diagnostics.append(
                    Diagnostic(
                        code="D306",
                        message=(
                            "Module docstring contains an Examples section but this "
                            "module is not configured as an API entry point"
                        ),
                        severity=context.policy.severity,
                        target=target.ref,
                        span=section.span,
                        fix=None,
                    )
                )

        return tuple(diagnostics)
