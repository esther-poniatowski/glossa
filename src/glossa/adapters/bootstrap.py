from __future__ import annotations

from pathlib import Path

from glossa.application.configuration import GlossaConfig, resolve_config
from glossa.application.registry import RuleRegistry, build_builtin_registry
from glossa.application.service import GlossaService
from glossa.errors import ConfigurationError
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
    plugin_rules: list[object] = []
    for provider in plugin_providers:
        plugin_rules.extend(provider.load_rules())
    if plugin_rules:
        registry = RuleRegistry(
            builtins=registry.builtins,
            plugins=tuple(plugin_rules),
        )

    _validate_rule_options(config, registry)

    return GlossaService(
        config=config,
        discovery=discovery,
        extractor=extractor,
        file_port=file_port,
        registry=registry,
    )


def _validate_rule_options(config: GlossaConfig, registry: RuleRegistry) -> None:
    """Validate user-supplied rule_options against each rule's option_schema."""
    for rule in registry.all_rules():
        name = rule.metadata.name
        user_options = config.rules.rule_options.get(name, {})
        for descriptor in rule.metadata.option_schema:
            if descriptor.key in user_options:
                path = f"rules.rule_options.{name}.{descriptor.key}"
                try:
                    descriptor.validator(user_options[descriptor.key], path)
                except ConfigurationError:
                    raise
                except Exception as exc:
                    raise ConfigurationError(
                        f"Invalid value for {path}: {exc}"
                    ) from exc
