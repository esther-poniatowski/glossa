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
        D100,
        D101,
        D102,
        D103,
        D104,
        D105,
        D106,
        D107,
        D108,
        D109,
        D110,
        D111,
    )
    from glossa.domain.rules.prose import (
        D200,
        D201,
        D202,
        D203,
        D204,
        D205,
    )
    from glossa.domain.rules.structure import (
        D300,
        D301,
        D302,
        D303,
        D304,
        D305,
        D306,
    )
    from glossa.domain.rules.typed_entries import (
        D400,
        D401,
        D402,
        D403,
        D404,
        D405,
    )
    from glossa.domain.rules.anti_patterns import (
        D500,
        D501,
        D502,
        D503,
    )

    builtins: tuple[Rule, ...] = (
        D100(),
        D101(),
        D102(),
        D103(),
        D104(),
        D105(),
        D106(),
        D107(),
        D108(),
        D109(),
        D110(),
        D111(),
        D200(),
        D201(),
        D202(),
        D203(),
        D204(),
        D205(),
        D300(),
        D301(),
        D302(),
        D303(),
        D304(),
        D305(),
        D306(),
        D400(),
        D401(),
        D402(),
        D403(),
        D404(),
        D405(),
        D500(),
        D501(),
        D502(),
        D503(),
    )

    return RuleRegistry(builtins=builtins, plugins=())
