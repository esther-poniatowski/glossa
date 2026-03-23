from __future__ import annotations

from importlib.metadata import entry_points

from glossa.application.protocols import RuleProvider
from glossa.errors import PluginLoadError


class EntryPointPluginLoader:
    """Load third-party rule providers from entry points."""

    def load_plugins(self) -> tuple[RuleProvider, ...]:
        providers: list[RuleProvider] = []
        eps = entry_points(group="glossa.rules")
        for ep in eps:
            try:
                provider_cls = ep.load()
                provider = provider_cls()
                providers.append(provider)
            except Exception as exc:
                raise PluginLoadError(
                    f"Failed to load plugin {ep.name!r}: {exc}"
                ) from exc
        return tuple(providers)
