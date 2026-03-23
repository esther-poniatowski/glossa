from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from glossa.application.contracts import GlossaConfig
from glossa.application.registry import RuleRegistry, build_builtin_registry
from glossa.infrastructure.config import ConfigLoader
from glossa.infrastructure.discovery import FileDiscovery
from glossa.infrastructure.extraction import ASTExtractor
from glossa.infrastructure.files import LocalFilePort
from glossa.infrastructure.plugins import EntryPointPluginLoader


@dataclass
class GlossaApp:
    """Assembled application with all dependencies wired."""
    config: GlossaConfig
    discovery: FileDiscovery
    extractor: ASTExtractor
    file_port: LocalFilePort
    registry: RuleRegistry


def bootstrap(
    base_path: Path | None = None,
    config_path: str | None = None,
) -> GlossaApp:
    """Build the fully-wired application."""
    if base_path is None:
        base_path = Path.cwd()

    # Load and resolve configuration
    loader = ConfigLoader(base_path)
    raw_config = loader.load(config_path)
    config = loader.resolve_config(raw_config)

    # Build infrastructure
    discovery = FileDiscovery(base_path)
    extractor = ASTExtractor()
    file_port = LocalFilePort(base_path)

    # Build rule registry with builtins + plugins
    registry = build_builtin_registry()
    plugin_loader = EntryPointPluginLoader()
    try:
        plugin_providers = plugin_loader.load_plugins()
        plugin_rules: list = []
        for provider in plugin_providers:
            plugin_rules.extend(provider.load_rules())
        if plugin_rules:
            registry = RuleRegistry(
                builtins=registry.builtins,
                plugins=tuple(plugin_rules),
            )
    except Exception:
        pass  # Plugin loading is best-effort in bootstrap

    return GlossaApp(
        config=config,
        discovery=discovery,
        extractor=extractor,
        file_port=file_port,
        registry=registry,
    )
