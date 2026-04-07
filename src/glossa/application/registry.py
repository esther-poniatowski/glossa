"""Rule registry and plugin loading orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from glossa.domain.rules import Rule


@dataclass(frozen=True)
class RuleRegistry:
    builtins: tuple[Rule, ...]
    plugins: tuple[Rule, ...]

    def all_rules(self) -> tuple[Rule, ...]:
        return self.builtins + self.plugins


def build_builtin_registry() -> RuleRegistry:
    """Instantiate all built-in rule classes and return a populated RuleRegistry.

    Imports rule classes from each sub-module under ``glossa.domain.rules``,
    instantiates each one, and bundles them into a :class:`RuleRegistry` with
    an empty plugins tuple.

    Returns
    -------
    RuleRegistry
        A registry containing all built-in rules and no plugin rules.
    """
    from glossa.domain.rules.presence import (
        MissingModuleDocstring,
        MissingClassDocstring,
        MissingCallableDocstring,
        MissingParametersSection,
        MissingReturnsSection,
        MissingYieldsSection,
        MissingRaisesSection,
        MissingWarnsSection,
        MissingModuleInventory,
        MissingAttributesSection,
        ParamsInInitNotClass,
        MissingDeprecationDirective,
    )
    from glossa.domain.rules.prose import (
        NonImperativeSummary,
        MissingPeriod,
        MissingBlankAfterSummary,
        FirstPersonVoice,
        SecondPersonVoice,
        MarkdownInDocstring,
    )
    from glossa.domain.rules.structure import (
        MalformedUnderline,
        SectionOrder,
        UndocumentedParameter,
        ExtraneousParameter,
        MalformedDeprecation,
        RstDirectiveInsteadOfSection,
        ExamplesInNonEntryModule,
    )
    from glossa.domain.rules.typed_entries import (
        MissingParamType,
        ParamTypeMismatch,
        MissingReturnType,
        ReturnTypeMismatch,
        YieldTypeMismatch,
        MissingAttributeType,
    )
    from glossa.domain.rules.anti_patterns import (
        EmptyDocstring,
        TrivialDunderDocstring,
        RedundantReturnsNone,
        RstNoteWarningDirective,
    )

    builtins: tuple[Rule, ...] = (
        MissingModuleDocstring(),
        MissingClassDocstring(),
        MissingCallableDocstring(),
        MissingParametersSection(),
        MissingReturnsSection(),
        MissingYieldsSection(),
        MissingRaisesSection(),
        MissingWarnsSection(),
        MissingModuleInventory(),
        MissingAttributesSection(),
        ParamsInInitNotClass(),
        MissingDeprecationDirective(),
        NonImperativeSummary(),
        MissingPeriod(),
        MissingBlankAfterSummary(),
        FirstPersonVoice(),
        SecondPersonVoice(),
        MarkdownInDocstring(),
        MalformedUnderline(),
        SectionOrder(),
        UndocumentedParameter(),
        ExtraneousParameter(),
        MalformedDeprecation(),
        RstDirectiveInsteadOfSection(),
        ExamplesInNonEntryModule(),
        MissingParamType(),
        ParamTypeMismatch(),
        MissingReturnType(),
        ReturnTypeMismatch(),
        YieldTypeMismatch(),
        MissingAttributeType(),
        EmptyDocstring(),
        TrivialDunderDocstring(),
        RedundantReturnsNone(),
        RstNoteWarningDirective(),
    )

    return RuleRegistry(builtins=builtins, plugins=())
