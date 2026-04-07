"""Section Structure and Placement rules for glossa."""

from __future__ import annotations

import fnmatch
import re

from glossa.domain.contracts import (
    ALL_TARGET_KINDS,
    CALLABLE_AND_CLASS_KINDS,
    Diagnostic,
    LintTarget,
    RuleOptionDescriptor,
    Severity,
    TargetKind,
)
from glossa.domain.models import (
    ProseSection,
    ProseSectionKind,
    SectionNode,
    TypedSection,
    TypedSectionKind,
    UnderlinedSectionProtocol,
    UnknownSection,
)
from glossa.domain.rules import RuleContext, RuleMetadata, make_diagnostic
from glossa.domain.rules._options import validate_string_tuple
from glossa.domain.rules._parameters import documentable_param_names
from glossa.domain.rules._scanning import scan_rst_directives

_GROUP = "structure"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _docstring_param_names(target: LintTarget) -> frozenset[str]:
    """Return parameter names listed in the Parameters section of *target*.

    Leading ``*`` / ``**`` prefixes are stripped so that docstring names like
    ``**kwargs`` match the bare ``kwargs`` stored in signature facts.
    """
    if target.docstring is None:
        return frozenset()
    params_section = target.docstring.typed_section(TypedSectionKind.PARAMETERS)
    if params_section is None:
        return frozenset()
    return frozenset(
        entry.name.lstrip("*")
        for entry in params_section.entries
        if entry.name is not None
    )


# ---------------------------------------------------------------------------
# malformed-underline
# ---------------------------------------------------------------------------


class MalformedUnderline:
    """Section underline is malformed."""

    metadata = RuleMetadata(
        name="malformed-underline",
        group=_GROUP,
        description="Section underline is malformed",
        default_severity=Severity.WARNING,
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
        docstring = target.docstring
        raw_body = docstring.syntax.raw_body
        diagnostics: list[Diagnostic] = []

        for section in docstring.sections:
            if not isinstance(section, UnderlinedSectionProtocol):
                continue

            title = section.section_title
            expected_len = len(title)

            ul_span = section.underline_span
            underline_text = raw_body[ul_span.start_offset : ul_span.end_offset]
            underline_stripped = underline_text.strip()

            malformed = (
                not underline_stripped
                or not re.fullmatch(r"-+", underline_stripped)
                or len(underline_stripped) != expected_len
            )

            if malformed:
                diagnostics.append(
                    make_diagnostic(
                        self, target, context,
                        f"Section '{title}' has a malformed underline: "
                        f"expected {expected_len} dashes, "
                        f"got {underline_stripped!r}",
                        span=ul_span,
                    )
                )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# section-order
# ---------------------------------------------------------------------------


class SectionOrder:
    """Section order violates NumPy policy."""

    metadata = RuleMetadata(
        name="section-order",
        group=_GROUP,
        description="Section order violates NumPy policy",
        default_severity=Severity.CONVENTION,
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
        sections = target.docstring.sections
        if not sections:
            return ()

        section_order = {title: idx for idx, title in enumerate(context.section_order)}

        ordered: list[tuple[int, SectionNode]] = []
        for section in sections:
            idx = section_order.get(section.section_title)
            if idx is not None:
                ordered.append((idx, section))

        diagnostics: list[Diagnostic] = []
        prev_idx = -1
        for idx, section in ordered:
            if idx < prev_idx:
                diagnostics.append(
                    make_diagnostic(
                        self, target, context,
                        f"Section '{section.section_title}' appears out of canonical NumPy order",
                        span=section.span,
                    )
                )
            else:
                prev_idx = idx

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# undocumented-parameter
# ---------------------------------------------------------------------------


class UndocumentedParameter:
    """Undocumented parameter present in signature."""

    metadata = RuleMetadata(
        name="undocumented-parameter",
        group=_GROUP,
        description="Undocumented parameter present in signature",
        default_severity=Severity.WARNING,
        applies_to=CALLABLE_AND_CLASS_KINDS,
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        sig_names = documentable_param_names(target)
        doc_names = _docstring_param_names(target)
        missing = sig_names - doc_names

        diagnostics: list[Diagnostic] = []
        for name in sorted(missing):
            diagnostics.append(
                make_diagnostic(
                    self, target, context,
                    f"Parameter '{name}' is in the signature but missing from the docstring",
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# extraneous-parameter
# ---------------------------------------------------------------------------


class ExtraneousParameter:
    """Extraneous parameter appears in docstring."""

    metadata = RuleMetadata(
        name="extraneous-parameter",
        group=_GROUP,
        description="Extraneous parameter appears in docstring",
        default_severity=Severity.WARNING,
        applies_to=CALLABLE_AND_CLASS_KINDS,
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        sig_names = documentable_param_names(target)
        doc_names = _docstring_param_names(target)
        extra = doc_names - sig_names

        diagnostics: list[Diagnostic] = []
        for name in sorted(extra):
            diagnostics.append(
                make_diagnostic(
                    self, target, context,
                    f"Parameter '{name}' appears in the docstring but not in the signature",
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# malformed-deprecation
# ---------------------------------------------------------------------------


class MalformedDeprecation:
    """Deprecation directive is malformed or misplaced."""

    metadata = RuleMetadata(
        name="malformed-deprecation",
        group=_GROUP,
        description="Deprecation directive is malformed or misplaced",
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
        deprecation = target.docstring.deprecation
        if deprecation is None:
            return ()

        diagnostics: list[Diagnostic] = []

        if deprecation.version is None:
            diagnostics.append(
                make_diagnostic(
                    self, target, context,
                    "Deprecation directive is missing a version",
                    span=deprecation.span,
                )
            )

        has_sections = len(target.docstring.sections) > 0
        extended_non_empty = any(
            line.strip()
            for line in target.docstring.extended_description_lines
        )
        if has_sections and extended_non_empty:
            diagnostics.append(
                make_diagnostic(
                    self, target, context,
                    "Deprecation directive should appear immediately after the "
                    "summary, before the extended description and sections",
                    span=deprecation.span,
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# rst-directive-instead-of-section
# ---------------------------------------------------------------------------

_RST_DIRECTIVE_SECTION_DIRECTIVES = frozenset({
    "seealso", "see-also", "admonition",
    "attention", "caution", "danger", "error", "hint", "important", "tip",
})


class RstDirectiveInsteadOfSection:
    """RST directive used where a NumPy section exists."""

    metadata = RuleMetadata(
        name="rst-directive-instead-of-section",
        group=_GROUP,
        description="RST directive used where a NumPy section exists",
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
        all_lines = target.docstring.all_text_lines()
        found = scan_rst_directives(all_lines, _RST_DIRECTIVE_SECTION_DIRECTIVES)
        if not found:
            return ()

        return tuple(
            make_diagnostic(
                self, target, context,
                f"RST directive found where a NumPy section should be used: "
                f"'.. {directive}::'",
            )
            for directive in found
        )


# ---------------------------------------------------------------------------
# examples-in-non-entry-module
# ---------------------------------------------------------------------------


class ExamplesInNonEntryModule:
    """Examples appears in a non-entry-point module docstring."""

    metadata = RuleMetadata(
        name="examples-in-non-entry-module",
        group=_GROUP,
        description="Examples appears in a non-entry-point module docstring",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({TargetKind.MODULE}),
        fixable=False,
        option_schema=(
            RuleOptionDescriptor("api_entry_modules", (), validate_string_tuple),
        ),
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()
        source_id = target.ref.source_id
        entry_modules: tuple[str, ...] = context.policy.options["api_entry_modules"]  # type: ignore[assignment]
        for pattern in entry_modules:
            if fnmatch.fnmatch(source_id, pattern):
                return ()

        diagnostics: list[Diagnostic] = []
        for section in target.docstring.sections:
            if (
                isinstance(section, ProseSection)
                and section.kind is ProseSectionKind.EXAMPLES
            ):
                diagnostics.append(
                    make_diagnostic(
                        self, target, context,
                        "Module docstring contains an Examples section but this "
                        "module is not configured as an API entry point",
                        span=section.span,
                    )
                )

        return tuple(diagnostics)
