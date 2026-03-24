"""D3xx — Section Structure and Placement rules for glossa."""

from __future__ import annotations

import fnmatch
import re

from glossa.core.contracts import Diagnostic, LintTarget, Severity, TargetKind
from glossa.domain.models import (
    ProseSection,
    ProseSectionKind,
    TypedSection,
    TypedSectionKind,
    UnknownSection,
)
from glossa.domain.rules import RuleContext, RuleMetadata, scan_rst_directives

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
        docstring = target.docstring
        raw_body = docstring.syntax.raw_body
        diagnostics: list[Diagnostic] = []

        for section in docstring.sections:
            if isinstance(section, UnknownSection):
                continue

            title = section.section_title
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
        sections = target.docstring.sections
        if not sections:
            return ()

        # Collect canonical indices for sections that have a known position.
        ordered: list[tuple[int, object]] = []
        for section in sections:
            idx = section.canonical_position
            if idx is not None:
                ordered.append((idx, section))

        # Check that canonical indices are non-decreasing.
        diagnostics: list[Diagnostic] = []
        prev_idx = -1
        for idx, section in ordered:
            if idx < prev_idx:
                title = section.section_title
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
    constructor = target.related.constructor
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

_D305_DIRECTIVES = frozenset({
    "note", "warning", "seealso", "see-also", "admonition",
    "attention", "caution", "danger", "error", "hint", "important", "tip",
})


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
        all_lines: list[str] = list(target.docstring.extended_description_lines)
        for section in target.docstring.sections:
            all_lines.extend(section.body_text_lines)

        found = scan_rst_directives(tuple(all_lines), _D305_DIRECTIVES)
        if not found:
            return ()

        return tuple(
            Diagnostic(
                code="D305",
                message=(
                    f"RST directive found where a NumPy section should be used: "
                    f"'.. {directive}::'"
                ),
                severity=context.policy.severity,
                target=target.ref,
                span=None,
                fix=None,
            )
            for directive in found
        )


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
        # Check whether this module is an API entry point.
        source_id = target.ref.source_id
        for pattern in context.policy.options.get("api_entry_modules", ()):
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
