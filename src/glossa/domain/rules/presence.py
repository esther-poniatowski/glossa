"""D1xx Presence and Coverage rules for the glossa docstring linter."""

from __future__ import annotations

from glossa.domain.rules import RuleMetadata, RuleContext
from glossa.core.contracts import Diagnostic, LintTarget, Severity, TargetKind, Visibility
from glossa.domain.models import TypedSectionKind, InventorySectionKind, TypedSection, InventorySection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _has_typed_section(docstring, kind: TypedSectionKind) -> bool:
    """Return True if docstring contains a TypedSection with the given kind."""
    return any(
        isinstance(section, TypedSection) and section.kind is kind
        for section in docstring.sections
    )


def _has_inventory_section(docstring, kind: InventorySectionKind) -> bool:
    """Return True if docstring contains an InventorySection with the given kind."""
    return any(
        isinstance(section, InventorySection) and section.kind is kind
        for section in docstring.sections
    )


def _documentable_params(target: LintTarget) -> list[str]:
    """Return parameter names from target.signature excluding 'self' and 'cls'."""
    if target.signature is None:
        return []
    return [
        p.name
        for p in target.signature.parameters
        if p.name not in ("self", "cls")
    ]


def _missing_docstring_check(
    target: LintTarget,
    context: RuleContext,
    kind: TargetKind,
    code: str,
    message: str,
) -> tuple[Diagnostic, ...]:
    """Shared logic for D100/D101: fire if a public target of *kind* has no docstring."""
    if target.kind is kind and target.visibility is Visibility.PUBLIC and target.docstring is None:
        return (
            Diagnostic(
                code=code,
                message=message,
                severity=context.policy.severity,
                target=target.ref,
                span=None,
            ),
        )
    return ()


# ---------------------------------------------------------------------------
# D100 — Missing public module docstring
# ---------------------------------------------------------------------------


class D100:
    """Missing public module docstring."""

    metadata = RuleMetadata(
        code="D100",
        description="Missing public module docstring.",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({TargetKind.MODULE}),
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        return _missing_docstring_check(
            target, context, TargetKind.MODULE, "D100", "Missing docstring in public module."
        )


# ---------------------------------------------------------------------------
# D101 — Missing public class docstring
# ---------------------------------------------------------------------------


class D101:
    """Missing public class docstring."""

    metadata = RuleMetadata(
        code="D101",
        description="Missing public class docstring.",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({TargetKind.CLASS}),
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        return _missing_docstring_check(
            target, context, TargetKind.CLASS, "D101", "Missing docstring in public class."
        )


# ---------------------------------------------------------------------------
# D102 — Missing public callable docstring
# ---------------------------------------------------------------------------


class D102:
    """Missing public callable docstring."""

    metadata = RuleMetadata(
        code="D102",
        description="Missing public callable docstring.",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.PROPERTY}),
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is not None:
            return ()

        include_test = context.policy.options.get("include_test_functions", False)
        if not include_test and target.is_test_target:
            return ()

        include_private = context.policy.options.get("include_private_helpers", False)
        if not include_private and target.visibility is Visibility.PRIVATE:
            return ()

        if target.visibility is Visibility.PUBLIC:
            return (
                Diagnostic(
                    code="D102",
                    message="Missing docstring in public callable.",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# D103 — Missing Parameters section for documentable parameters
# ---------------------------------------------------------------------------


class D103:
    """Missing Parameters section for documentable parameters."""

    metadata = RuleMetadata(
        code="D103",
        description="Missing Parameters section for documentable parameters.",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.CLASS}),
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        params = _documentable_params(target)

        # For CLASS targets with no params on the class signature, check the
        # related constructor's signature instead.
        if target.kind is TargetKind.CLASS and not params:
            constructor = target.related.get("constructor")
            if constructor is not None and constructor.signature is not None:
                params = [
                    p.name
                    for p in constructor.signature.parameters
                    if p.name not in ("self", "cls")
                ]

        if not params:
            return ()

        if not _has_typed_section(target.docstring, TypedSectionKind.PARAMETERS):
            return (
                Diagnostic(
                    code="D103",
                    message="Missing Parameters section for documentable parameters.",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# D104 — Missing Returns section where required
# ---------------------------------------------------------------------------


class D104:
    """Missing Returns section where required."""

    metadata = RuleMetadata(
        code="D104",
        description="Missing Returns section where required.",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.PROPERTY}),
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()
        if target.signature is None:
            return ()
        if not target.signature.returns_value:
            return ()

        # For PROPERTY targets, check option before firing.
        if target.kind is TargetKind.PROPERTY:
            if not context.policy.options.get("simple_property_requires_returns", True):
                return ()

        if not _has_typed_section(target.docstring, TypedSectionKind.RETURNS):
            return (
                Diagnostic(
                    code="D104",
                    message="Missing Returns section where required.",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# D105 — Missing Yields section for generators
# ---------------------------------------------------------------------------


class D105:
    """Missing Yields section for generators."""

    metadata = RuleMetadata(
        code="D105",
        description="Missing Yields section for generators.",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.PROPERTY}),
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()
        if target.signature is None:
            return ()
        if not target.signature.yields_value:
            return ()

        if not _has_typed_section(target.docstring, TypedSectionKind.YIELDS):
            return (
                Diagnostic(
                    code="D105",
                    message="Missing Yields section for generator.",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# D106 — Missing Raises section for public-contract exceptions
# ---------------------------------------------------------------------------


class D106:
    """Missing Raises section for public-contract exceptions."""

    metadata = RuleMetadata(
        code="D106",
        description="Missing Raises section for public-contract exceptions.",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.PROPERTY}),
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        high_confidence = [
            exc
            for exc in target.exceptions
            if exc.confidence == "high" and exc.evidence != "reraise"
        ]
        if not high_confidence:
            return ()

        if not _has_typed_section(target.docstring, TypedSectionKind.RAISES):
            return (
                Diagnostic(
                    code="D106",
                    message="Missing Raises section for public-contract exceptions.",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# D107 — Missing Warns section for public warnings
# ---------------------------------------------------------------------------


class D107:
    """Missing Warns section for public warnings."""

    metadata = RuleMetadata(
        code="D107",
        description="Missing Warns section for public warnings.",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.PROPERTY}),
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        high_confidence = [
            w for w in target.warnings if w.confidence == "high"
        ]
        if not high_confidence:
            return ()

        if not _has_typed_section(target.docstring, TypedSectionKind.WARNS):
            return (
                Diagnostic(
                    code="D107",
                    message="Missing Warns section for public warnings.",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# D108 — Missing module Classes/Functions inventory when required
# ---------------------------------------------------------------------------


class D108:
    """Missing module Classes/Functions inventory when required."""

    metadata = RuleMetadata(
        code="D108",
        description="Missing module Classes/Functions inventory when required.",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({TargetKind.MODULE}),
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        threshold = context.policy.options.get("inventory_threshold", 2)

        public_classes = sum(
            1
            for sym in target.module_symbols
            if sym.kind == "class" and sym.is_public
        )
        public_functions = sum(
            1
            for sym in target.module_symbols
            if sym.kind == "function" and sym.is_public
        )

        diagnostics: list[Diagnostic] = []

        if public_classes >= threshold and not _has_inventory_section(
            target.docstring, InventorySectionKind.CLASSES
        ):
            diagnostics.append(
                Diagnostic(
                    code="D108",
                    message="Missing Classes inventory section in module docstring.",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                )
            )

        if public_functions >= threshold and not _has_inventory_section(
            target.docstring, InventorySectionKind.FUNCTIONS
        ):
            diagnostics.append(
                Diagnostic(
                    code="D108",
                    message="Missing Functions inventory section in module docstring.",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# D109 — Missing Attributes section where class attributes require documentation
# ---------------------------------------------------------------------------


class D109:
    """Missing Attributes section where class attributes require documentation."""

    metadata = RuleMetadata(
        code="D109",
        description="Missing Attributes section where class attributes require documentation.",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.CLASS}),
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        public_attrs = [a for a in target.attributes if a.is_public]
        if not public_attrs:
            return ()

        if not _has_typed_section(target.docstring, TypedSectionKind.ATTRIBUTES):
            return (
                Diagnostic(
                    code="D109",
                    message="Missing Attributes section for public class attributes.",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# D110 — Constructor parameters documented in __init__ instead of class docstring
# ---------------------------------------------------------------------------


class D110:
    """Constructor parameters documented in __init__ instead of class docstring."""

    metadata = RuleMetadata(
        code="D110",
        description="Constructor parameters documented in __init__ instead of class docstring.",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.CLASS}),
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        constructor = target.related.get("constructor")
        if constructor is None:
            return ()

        constructor_has_params_section = (
            constructor.docstring is not None
            and _has_typed_section(constructor.docstring, TypedSectionKind.PARAMETERS)
        )
        class_has_params_section = _has_typed_section(
            target.docstring, TypedSectionKind.PARAMETERS
        )

        if constructor_has_params_section and not class_has_params_section:
            return (
                Diagnostic(
                    code="D110",
                    message=(
                        "Constructor parameters are documented in __init__ "
                        "instead of the class docstring."
                    ),
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# D111 — Missing deprecation directive for deprecated public API
# ---------------------------------------------------------------------------


class D111:
    """Missing deprecation directive for deprecated public API."""

    metadata = RuleMetadata(
        code="D111",
        description="Missing deprecation directive for deprecated public API.",
        default_severity=Severity.WARNING,
        applies_to=frozenset({
            TargetKind.MODULE,
            TargetKind.CLASS,
            TargetKind.FUNCTION,
            TargetKind.METHOD,
            TargetKind.PROPERTY,
        }),
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()

        has_deprecated_decorator = any(
            "deprecated" in dec.lower() for dec in target.decorators
        )
        if not has_deprecated_decorator:
            return ()

        if target.docstring.deprecation is None:
            return (
                Diagnostic(
                    code="D111",
                    message=(
                        "Deprecated public API is missing a deprecation directive "
                        "in its docstring."
                    ),
                    severity=context.policy.severity,
                    target=target.ref,
                    span=None,
                ),
            )
        return ()
