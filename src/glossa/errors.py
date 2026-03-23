"""Exception hierarchy for operational failures."""

from __future__ import annotations


class GlossaError(Exception):
    ...


class ConfigurationError(GlossaError):
    ...


class DiscoveryError(GlossaError):
    ...


class ExtractionError(GlossaError):
    ...


class DocstringParseError(GlossaError):
    ...


class FixConflictError(GlossaError):
    ...


class ValidationError(GlossaError):
    ...


class FileWriteError(GlossaError):
    ...


class PluginLoadError(GlossaError):
    ...
