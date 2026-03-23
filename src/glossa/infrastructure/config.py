from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from glossa.application.contracts import (
    FixPolicy,
    GlossaConfig,
    OutputOptions,
    RuleSelection,
    Severity,
    SuppressionPolicy,
)
from glossa.errors import ConfigurationError

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib  # type: ignore[no-redef]
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError as exc:
            raise ImportError(
                "tomllib is required on Python < 3.11; install tomli: pip install tomli"
            ) from exc


class ConfigLoader:
    """Load glossa configuration from pyproject.toml or .glossa.yaml."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def load(self, config_path: str | None = None) -> dict[str, object]:
        """Return raw configuration dictionary.

        Parameters
        ----------
        config_path : str | None, optional
            Explicit path to a configuration file. When ``None``, search for
            ``pyproject.toml`` then ``.glossa.yaml`` under the base path.

        Returns
        -------
        dict[str, object]
            Raw, unvalidated configuration data. An empty dict is returned
            when no configuration file is found.

        Raises
        ------
        ConfigurationError
            If the specified or discovered file cannot be read or parsed.
        """
        if config_path is not None:
            path = Path(config_path)
            if not path.is_absolute():
                path = self._base_path / config_path
            return self._load_file(path)

        pyproject = self._base_path / "pyproject.toml"
        if pyproject.exists():
            return self._load_file(pyproject)

        glossa_yaml = self._base_path / ".glossa.yaml"
        if glossa_yaml.exists():
            return self._load_file(glossa_yaml)

        return {}

    def _load_file(self, path: Path) -> dict[str, object]:
        try:
            if path.suffix == ".toml":
                with path.open("rb") as fh:
                    data = tomllib.load(fh)
                return data.get("tool", {}).get("glossa", {})  # type: ignore[return-value]
            elif path.suffix in (".yaml", ".yml"):
                with path.open(encoding="utf-8") as fh:
                    data = yaml.safe_load(fh) or {}
                if not isinstance(data, dict):
                    raise ConfigurationError(
                        f"Expected a mapping at the top level of {path}"
                    )
                return data  # type: ignore[return-value]
            else:
                raise ConfigurationError(
                    f"Unsupported configuration file format: {path.suffix!r}"
                )
        except ConfigurationError:
            raise
        except Exception as exc:
            raise ConfigurationError(
                f"Failed to load configuration from {path}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Resolver
    # ------------------------------------------------------------------

    def resolve_config(self, raw: dict[str, object]) -> GlossaConfig:
        """Convert a raw config dict into a typed ``GlossaConfig``.

        Parameters
        ----------
        raw : dict[str, object]
            Unvalidated configuration dictionary as returned by ``load()``.

        Returns
        -------
        GlossaConfig
            Fully validated, typed configuration object with defaults applied.
        """
        rules_raw: dict[str, Any] = raw.get("rules", {})  # type: ignore[assignment]
        suppressions_raw: dict[str, Any] = raw.get("suppressions", {})  # type: ignore[assignment]
        fix_raw: dict[str, Any] = raw.get("fix", {})  # type: ignore[assignment]
        output_raw: dict[str, Any] = raw.get("output", {})  # type: ignore[assignment]

        # --- RuleSelection ---
        select_raw = rules_raw.get("select", ("D1xx", "D2xx", "D3xx", "D4xx", "D5xx"))
        ignore_raw = rules_raw.get("ignore", ())
        severity_overrides_raw: dict[str, str] = rules_raw.get("severity_overrides", {})
        per_file_ignores_raw: dict[str, list[str]] = rules_raw.get("per_file_ignores", {})
        rule_options_raw: dict[str, dict[str, object]] = rules_raw.get("rule_options", {})

        severity_overrides = {
            k: Severity(v) for k, v in severity_overrides_raw.items()
        }
        per_file_ignores = {
            k: tuple(v) for k, v in per_file_ignores_raw.items()
        }

        rules = RuleSelection(
            select=tuple(select_raw),
            ignore=tuple(ignore_raw),
            severity_overrides=severity_overrides,
            per_file_ignores=per_file_ignores,
            rule_options={k: dict(v) for k, v in rule_options_raw.items()},
        )

        # --- SuppressionPolicy ---
        suppressions = SuppressionPolicy(
            inline_enabled=suppressions_raw.get("inline_enabled", True),
            directive_prefix=suppressions_raw.get("directive_prefix", "glossa: ignore="),
        )

        # --- FixPolicy ---
        fix = FixPolicy(
            enabled=fix_raw.get("enabled", True),
            apply=fix_raw.get("apply", "safe"),  # type: ignore[arg-type]
            validate_after_apply=fix_raw.get("validate_after_apply", True),
        )

        # --- OutputOptions ---
        output = OutputOptions(
            format=output_raw.get("format", "text"),  # type: ignore[arg-type]
            color=output_raw.get("color", True),
            show_source=output_raw.get("show_source", True),
        )

        return GlossaConfig(
            rules=rules,
            suppressions=suppressions,
            fix=fix,
            output=output,
        )
