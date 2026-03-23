from __future__ import annotations

from pathlib import Path

from glossa.application.configuration import resolve_config
from glossa.application.registry import RuleRegistry, build_builtin_registry
from glossa.application.service import GlossaService
from glossa.infrastructure.config import ConfigLoader
from glossa.infrastructure.discovery import FileDiscovery
from glossa.infrastructure.extraction import ASTExtractor
from glossa.infrastructure.files import LocalFilePort
from glossa.infrastructure.plugins import EntryPointPluginLoader


def bootstrap(
    base_path: Path | None = None,
    config_path: str | None = None,
) -> GlossaService:
    """Build the fully-wired application service."""
    if base_path is None:
        base_path = Path.cwd()

    loader = ConfigLoader(base_path)
    raw_config = loader.load(config_path)
    config = resolve_config(raw_config)

    discovery = FileDiscovery(base_path)
    extractor = ASTExtractor()
    file_port = LocalFilePort(base_path)

    registry = build_builtin_registry()
    plugin_loader = EntryPointPluginLoader()
    plugin_providers = plugin_loader.load_plugins()
    plugin_rules: list = []
    for provider in plugin_providers:
        plugin_rules.extend(provider.load_rules())
    if plugin_rules:
        registry = RuleRegistry(
            builtins=registry.builtins,
            plugins=tuple(plugin_rules),
        )

    return GlossaService(
        config=config,
        discovery=discovery,
        extractor=extractor,
        file_port=file_port,
        registry=registry,
    )


def create_linter(
    base_path: Path | None = None,
    config_path: str | None = None,
) -> GlossaService:
    """Backward-compatible factory for the programmatic API."""
    return bootstrap(base_path=base_path, config_path=config_path)
