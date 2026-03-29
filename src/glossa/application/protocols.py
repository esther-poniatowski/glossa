"""Ports (Protocol classes) that infrastructure adapters must satisfy.

Each protocol in this module represents a dependency boundary: the application
layer declares *what* it needs; infrastructure layers provide conforming
implementations without the application importing them directly.

Protocols
---------
DiscoveryPort
    Discovers Python source files within a set of paths.
ExtractionPort
    Extracts lintable targets from a Python source file.
FilePort
    Reads and writes source file content.
ConfigPort
    Loads raw configuration data from pyproject.toml or .glossa.yaml.
PluginPort
    Discovers and loads third-party rule providers via entry points.
RuleProvider
    Supplies a set of lint rules (used by PluginPort).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Protocol, Sequence, runtime_checkable

if TYPE_CHECKING:
    from glossa.domain.contracts import ExtractedTarget
    from glossa.domain.rules import Rule


# ---------------------------------------------------------------------------
# Rule Provider
# ---------------------------------------------------------------------------


@runtime_checkable
class RuleProvider(Protocol):
    """Supplies a collection of lint rules.

    Implemented by third-party plugins that register rules for glossa to
    discover via entry points.
    """

    def load_rules(self) -> tuple[Rule, ...]:
        """Return all rules provided by this plugin.

        Returns
        -------
        tuple[Rule, ...]
            Tuple of rule objects contributed by this provider.
        """
        ...


# ---------------------------------------------------------------------------
# Infrastructure Ports
# ---------------------------------------------------------------------------


@runtime_checkable
class DiscoveryPort(Protocol):
    """Discovers Python source files under a set of root paths.

    Implementations are responsible for recursing into directories,
    filtering by file extension, and honouring any exclusion patterns.
    """

    def discover(
        self,
        paths: Sequence[str],
        exclude: Sequence[str] = (),
    ) -> Iterator[str]:
        """Yield project-relative POSIX path strings for Python source files.

        Parameters
        ----------
        paths : Sequence[str]
            Root paths (files or directories) to search.
        exclude : Sequence[str], optional
            Glob patterns for paths that should be skipped.

        Yields
        ------
        str
            Project-relative POSIX path string for each discovered Python
            source file.
        """
        ...


@runtime_checkable
class ExtractionPort(Protocol):
    """Extracts lintable targets from a Python source file.

    Implementations parse the source text and produce a flat sequence of
    ``ExtractedTarget`` objects, one per documentable symbol.
    """

    def extract(
        self,
        source_id: str,
        source_text: str,
    ) -> tuple[ExtractedTarget, ...]:
        """Parse a Python source file and return extracted targets.

        Parameters
        ----------
        source_id : str
            Project-relative POSIX path that uniquely identifies the source
            file (used to populate ``SourceRef`` values inside the results).
        source_text : str
            Full text content of the source file.

        Returns
        -------
        tuple[ExtractedTarget, ...]
            One ``ExtractedTarget`` per documentable symbol found in the
            source file.
        """
        ...


@runtime_checkable
class FilePort(Protocol):
    """Reads and writes source file content.

    Implementations handle the I/O mechanics (encoding, path resolution,
    atomic writes, etc.) so that the application layer stays pure.
    """

    def read(self, source_id: str) -> str:
        """Return the text content of a source file.

        Parameters
        ----------
        source_id : str
            Project-relative POSIX path identifying the file to read.

        Returns
        -------
        str
            Full decoded text content of the file.
        """
        ...

    def write(self, source_id: str, content: str) -> None:
        """Write content to a source file.

        Parameters
        ----------
        source_id : str
            Project-relative POSIX path identifying the file to write.
        content : str
            Text content to write to the file.
        """
        ...


@runtime_checkable
class ConfigPort(Protocol):
    """Loads raw configuration data for glossa.

    Implementations locate and parse ``pyproject.toml`` (``[tool.glossa]``
    section) or ``.glossa.yaml``, returning an unvalidated dictionary that
    the application layer can then map onto ``GlossaConfig``.
    """

    def load(self, config_path: str | None = None) -> dict[str, object]:
        """Return raw configuration dictionary.

        Parameters
        ----------
        config_path : str | None, optional
            Explicit path to a configuration file.  When ``None``,
            implementations should search for ``pyproject.toml`` or
            ``.glossa.yaml`` starting from the current working directory.

        Returns
        -------
        dict[str, object]
            Raw, unvalidated configuration data.  An empty dict is returned
            when no configuration file is found.
        """
        ...


@runtime_checkable
class PluginPort(Protocol):
    """Discovers and loads third-party rule providers.

    Implementations use Python entry points (or an equivalent mechanism) to
    find installed packages that advertise glossa rule providers.
    """

    def load_plugins(self) -> tuple[RuleProvider, ...]:
        """Return rule providers discovered via entry points.

        Returns
        -------
        tuple[RuleProvider, ...]
            One ``RuleProvider`` instance per registered plugin.  Returns an
            empty tuple when no plugins are installed.
        """
        ...
