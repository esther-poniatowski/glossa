"""Resolve the root of a project and load the glossa settings file.

The root is resolved in this order: the option ``--root``, the environment
variable ``GLOSSA_ROOT``, the nearest ancestor of the current folder that holds
a settings file, and the current folder. The settings file is
``config/tools/glossa.yml`` or ``glossa.yml`` below the root, or the same names
with the extension ``.toml``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping

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


ROOT_VARIABLE = "GLOSSA_ROOT"
"""Environment variable naming the root when ``--root`` is absent."""

SETTINGS_NAMES: tuple[str, ...] = ("glossa.yml", "glossa.toml")
"""Names of the settings file: one in YAML, one in TOML."""

SETTINGS_FOLDER = Path("config", "tools")
"""Folder below the root that may hold the settings file."""


def settings_candidates(folder: Path) -> list[Path]:
    """Return the settings files that exist below *folder*.

    Parameters
    ----------
    folder : Path
        Folder searched in ``config/tools/`` and at its own level.

    Returns
    -------
    list[Path]
        Existing settings files, those of ``config/tools/`` first.
    """
    places = (folder / SETTINGS_FOLDER, folder)
    return [place / name for place in places for name in SETTINGS_NAMES if (place / name).is_file()]


def resolve_root(
    option: Path | None,
    environ: Mapping[str, str],
    cwd: Path,
) -> Path:
    """Return the root of the project, resolved in the order of the conventions.

    Parameters
    ----------
    option : Path | None
        Value of ``--root``, relative to *cwd* when it is not absolute.
    environ : Mapping[str, str]
        Environment, read for ``GLOSSA_ROOT``.
    cwd : Path
        Current folder.

    Returns
    -------
    Path
        Absolute path of the root: the option, then the environment variable,
        then the nearest ancestor of *cwd* holding a settings file, then *cwd*.

    Raises
    ------
    ConfigurationError
        If the folder named by the option or by the variable does not exist.
    """
    if option is not None:
        return _existing_folder(cwd / option, "--root")
    value = environ.get(ROOT_VARIABLE)
    if value:
        return _existing_folder(cwd / value, ROOT_VARIABLE)
    cwd = cwd.resolve()
    for folder in (cwd, *cwd.parents):
        if settings_candidates(folder):
            return folder
    return cwd


def _existing_folder(path: Path, source: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_dir():
        raise ConfigurationError(f"The root named by {source} is not a folder: {path}")
    return resolved


class ConfigLoader:
    """Load the glossa settings file of a root."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def load(self, config_path: str | None = None) -> dict[str, object]:
        """Return raw configuration dictionary.

        Parameters
        ----------
        config_path : str | None, optional
            Explicit path to a settings file, relative to the current folder.
            When ``None``, read ``config/tools/glossa.<ext>`` or
            ``glossa.<ext>`` below the root, where ``<ext>`` is ``yml`` or
            ``toml``.

        Returns
        -------
        dict[str, object]
            Raw, unvalidated configuration data. An empty dict is returned
            when no settings file exists below the root.

        Raises
        ------
        ConfigurationError
            If the explicit file does not exist, if several settings files
            exist below the root, or if the file cannot be read or parsed.
        """
        if config_path is not None:
            path = Path(config_path)
            if not path.is_file():
                raise ConfigurationError(f"The settings file does not exist: {config_path}")
            return self._load_file(path)

        candidates = settings_candidates(self._base_path)
        if len(candidates) > 1:
            names = ", ".join(str(candidate) for candidate in candidates)
            raise ConfigurationError(f"Several settings files compete: {names}")
        if candidates:
            return self._load_file(candidates[0])
        return {}

    def _load_file(self, path: Path) -> dict[str, object]:
        try:
            if path.suffix == ".toml":
                with path.open("rb") as fh:
                    return tomllib.load(fh)
            elif path.suffix in (".yaml", ".yml"):
                with path.open(encoding="utf-8") as fh:
                    data = yaml.safe_load(fh) or {}
                if not isinstance(data, dict):
                    raise ConfigurationError(
                        f"Expected a mapping at the top level of {path}"
                    )
                return data
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
