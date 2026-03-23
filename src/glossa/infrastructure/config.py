from __future__ import annotations

import sys
from pathlib import Path

import yaml
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
