"""Presence and Coverage rules for the glossa docstring linter."""

from __future__ import annotations

from typing import Callable, cast

from glossa.domain.contracts import (
    ALL_TARGET_KINDS,
    CALLABLE_TARGET_KINDS,
    Confidence,
    Diagnostic,
    ExceptionEvidence,
    ExceptionFact,
    LintTarget,
    RuleOptionDescriptor,
    Severity,
    SignatureFacts,
    TargetKind,
    Visibility,
    WarningFact,
)
from glossa.domain.models import InventorySectionKind, TypedSectionKind
from glossa.domain.rules import Rule, RuleContext, RuleMetadata, make_diagnostic
from glossa.domain.rules._options import validate_bool, validate_positive_int
from glossa.domain.rules._parameters import documentable_param_names

_GROUP = "presence"


# ---------------------------------------------------------------------------
# Parameterized rule factories
# ---------------------------------------------------------------------------


def _make_missing_docstring_rule(
    kind: TargetKind,
    name: str,
    description: str,
    message: str,
) -> type[Rule]:
    """Factory: fire if a public target of *kind* has no docstring."""

    class _Rule:
        metadata = RuleMetadata(
            name=name,
            group=_GROUP,
            description=description,
            default_severity=Severity.CONVENTION,
            applies_to=frozenset({kind}),
            fixable=False,
            requires_docstring=False,
        )

        def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
            if (
                target.kind is kind
                and target.visibility is Visibility.PUBLIC
                and target.docstring is None
            ):
                return (make_diagnostic(self, target, context, message),)
            return ()

    _Rule.__name__ = name
    _Rule.__qualname__ = name
    _Rule.__doc__ = description
    return _Rule


def _make_missing_section_rule(
    name: str,
    description: str,
    message: str,
    section_kind: TypedSectionKind,
    signature_predicate: Callable[[SignatureFacts], bool],
    applies_to: frozenset[TargetKind],
    option_key: str | None = None,
    option_schema: tuple[RuleOptionDescriptor, ...] = (),
) -> type[Rule]:
    """Factory: fire if a signature predicate is True but section is missing."""

    class _Rule:
        metadata = RuleMetadata(
            name=name,
            group=_GROUP,
            description=description,
            default_severity=Severity.WARNING,
            applies_to=applies_to,
            fixable=True,
            option_schema=option_schema,
        )

        def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
            if target.docstring is None or target.signature is None:
                return ()
            if not signature_predicate(target.signature):
                return ()

            if option_key is not None and target.kind is TargetKind.PROPERTY:
                if not context.policy.options[option_key]:
                    return ()

            if not target.docstring.has_typed_section(section_kind):
                return (make_diagnostic(self, target, context, message),)
            return ()

    _Rule.__name__ = name
    _Rule.__qualname__ = name
    _Rule.__doc__ = description
    return _Rule


def _make_missing_fact_section_rule(
    name: str,
    description: str,
    message: str,
    fact_accessor: Callable[[LintTarget], tuple[ExceptionFact, ...] | tuple[WarningFact, ...]],
    section_kind: TypedSectionKind,
    confidence_filter: Confidence = Confidence.HIGH,
    exclude_evidence: ExceptionEvidence | None = None,
) -> type[Rule]:
    """Factory: fire if high-confidence facts exist but section is missing."""

    class _Rule:
        metadata = RuleMetadata(
            name=name,
            group=_GROUP,
            description=description,
            default_severity=Severity.WARNING,
            applies_to=CALLABLE_TARGET_KINDS,
            fixable=False,
        )

        def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
            if target.docstring is None:
                return ()
            facts = fact_accessor(target)
            relevant = [
                f for f in facts
                if f.confidence is confidence_filter
                and not (
                    exclude_evidence is not None
                    and isinstance(f, ExceptionFact)
                    and f.evidence is exclude_evidence
                )
            ]
            if not relevant:
                return ()

            if not target.docstring.has_typed_section(section_kind):
                return (make_diagnostic(self, target, context, message),)
            return ()

    _Rule.__name__ = name
    _Rule.__qualname__ = name
    _Rule.__doc__ = description
    return _Rule


# ---------------------------------------------------------------------------
# missing-module-docstring
# ---------------------------------------------------------------------------

D100 = _make_missing_docstring_rule(
    kind=TargetKind.MODULE,
    name="missing-module-docstring",
    description="Missing public module docstring.",
    message="Missing docstring in public module.",
)


# ---------------------------------------------------------------------------
# missing-class-docstring
# ---------------------------------------------------------------------------

D101 = _make_missing_docstring_rule(
    kind=TargetKind.CLASS,
    name="missing-class-docstring",
    description="Missing public class docstring.",
    message="Missing docstring in public class.",
)


# ---------------------------------------------------------------------------
# missing-callable-docstring
# ---------------------------------------------------------------------------


class D102:
    """Missing public callable docstring."""

    metadata = RuleMetadata(
        name="missing-callable-docstring",
        group=_GROUP,
        description="Missing public callable docstring.",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.PROPERTY}),
        fixable=False,
        requires_docstring=False,
        option_schema=(
            RuleOptionDescriptor("include_test_functions", False, validate_bool),
            RuleOptionDescriptor("include_private_helpers", False, validate_bool),
        ),
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is not None:
            return ()

        include_test = context.policy.options["include_test_functions"]
        if not include_test and target.is_test_target:
            return ()

        include_private = context.policy.options["include_private_helpers"]
        if not include_private and target.visibility is Visibility.PRIVATE:
            return ()

        if target.visibility is Visibility.PUBLIC:
            return (make_diagnostic(self, target, context, "Missing docstring in public callable."),)
        return ()


# ---------------------------------------------------------------------------
# missing-parameters-section
# ---------------------------------------------------------------------------


class D103:
    """Missing Parameters section for documentable parameters."""

    metadata = RuleMetadata(
        name="missing-parameters-section",
        group=_GROUP,
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
        if not documentable_param_names(target):
            return ()

        if target.docstring is None or not target.docstring.has_typed_section(TypedSectionKind.PARAMETERS):
            return (
                make_diagnostic(
                    self, target, context,
                    "Missing Parameters section for documentable parameters.",
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# missing-returns-section
# ---------------------------------------------------------------------------

D104 = _make_missing_section_rule(
    name="missing-returns-section",
    description="Missing Returns section where required.",
    message="Missing Returns section where required.",
    section_kind=TypedSectionKind.RETURNS,
    signature_predicate=lambda s: s.returns_value,
    applies_to=CALLABLE_TARGET_KINDS,
    option_key="simple_property_requires_returns",
    option_schema=(
        RuleOptionDescriptor("simple_property_requires_returns", True, validate_bool),
    ),
)


# ---------------------------------------------------------------------------
# missing-yields-section
# ---------------------------------------------------------------------------

D105 = _make_missing_section_rule(
    name="missing-yields-section",
    description="Missing Yields section for generators.",
    message="Missing Yields section for generator.",
    section_kind=TypedSectionKind.YIELDS,
    signature_predicate=lambda s: s.yields_value,
    applies_to=CALLABLE_TARGET_KINDS,
)


# ---------------------------------------------------------------------------
# missing-raises-section
# ---------------------------------------------------------------------------

D106 = _make_missing_fact_section_rule(
    name="missing-raises-section",
    description="Missing Raises section for public-contract exceptions.",
    message="Missing Raises section for public-contract exceptions.",
    fact_accessor=lambda t: t.exceptions,
    section_kind=TypedSectionKind.RAISES,
    confidence_filter=Confidence.HIGH,
    exclude_evidence=ExceptionEvidence.RERAISE,
)


# ---------------------------------------------------------------------------
# missing-warns-section
# ---------------------------------------------------------------------------

D107 = _make_missing_fact_section_rule(
    name="missing-warns-section",
    description="Missing Warns section for public warnings.",
    message="Missing Warns section for public warnings.",
    fact_accessor=lambda t: t.warnings,
    section_kind=TypedSectionKind.WARNS,
    confidence_filter=Confidence.HIGH,
)


# ---------------------------------------------------------------------------
# missing-module-inventory
# ---------------------------------------------------------------------------


class D108:
    """Missing module Classes/Functions inventory when required."""

    metadata = RuleMetadata(
        name="missing-module-inventory",
        group=_GROUP,
        description="Missing module Classes/Functions inventory when required.",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({TargetKind.MODULE}),
        fixable=True,
        option_schema=(
            RuleOptionDescriptor("inventory_threshold", 2, validate_positive_int),
        ),
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:

        threshold = cast(int, context.policy.options["inventory_threshold"])

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

        if target.docstring is None:
            return ()

        diagnostics: list[Diagnostic] = []

        if public_classes >= threshold and not target.docstring.has_inventory_section(
            InventorySectionKind.CLASSES
        ):
            diagnostics.append(
                make_diagnostic(
                    self, target, context,
                    "Missing Classes inventory section in module docstring.",
                )
            )

        if public_functions >= threshold and not target.docstring.has_inventory_section(
            InventorySectionKind.FUNCTIONS
        ):
            diagnostics.append(
                make_diagnostic(
                    self, target, context,
                    "Missing Functions inventory section in module docstring.",
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# missing-attributes-section
# ---------------------------------------------------------------------------


class D109:
    """Missing Attributes section where class attributes require documentation."""

    metadata = RuleMetadata(
        name="missing-attributes-section",
        group=_GROUP,
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

        public_attrs = [a for a in target.attributes if a.is_public]
        if not public_attrs:
            return ()

        if target.docstring is None or not target.docstring.has_typed_section(TypedSectionKind.ATTRIBUTES):
            return (
                make_diagnostic(
                    self, target, context,
                    "Missing Attributes section for public class attributes.",
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# params-in-init-not-class
# ---------------------------------------------------------------------------


class D110:
    """Constructor parameters documented in __init__ instead of class docstring."""

    metadata = RuleMetadata(
        name="params-in-init-not-class",
        group=_GROUP,
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

        constructor = target.related.constructor
        if constructor is None:
            return ()

        constructor_has_params_section = (
            constructor.docstring is not None
            and constructor.docstring.has_typed_section(TypedSectionKind.PARAMETERS)
        )
        class_has_params_section = (
            target.docstring is not None
            and target.docstring.has_typed_section(TypedSectionKind.PARAMETERS)
        )

        if constructor_has_params_section and not class_has_params_section:
            return (
                make_diagnostic(
                    self, target, context,
                    "Constructor parameters are documented in __init__ "
                    "instead of the class docstring.",
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# missing-deprecation-directive
# ---------------------------------------------------------------------------


class D111:
    """Missing deprecation directive for deprecated public API."""

    metadata = RuleMetadata(
        name="missing-deprecation-directive",
        group=_GROUP,
        description="Missing deprecation directive for deprecated public API.",
        default_severity=Severity.WARNING,
        applies_to=ALL_TARGET_KINDS,
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:

        has_deprecated_decorator = any(
            "deprecated" in dec.lower() for dec in target.decorators
        )
        if not has_deprecated_decorator:
            return ()

        if target.docstring is None or target.docstring.deprecation is None:
            return (
                make_diagnostic(
                    self, target, context,
                    "Deprecated public API is missing a deprecation directive "
                    "in its docstring.",
                ),
            )
        return ()
