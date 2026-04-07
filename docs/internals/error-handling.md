# Error Handling and Robustness

Operational failures are not lint diagnostics. They are explicit tool errors with
a structured exception hierarchy, defined failure semantics, and deterministic exit
codes.

## Exception Hierarchy

```python
class GlossaError(Exception): ...
class ConfigurationError(GlossaError): ...
class DiscoveryError(GlossaError): ...
class ExtractionError(GlossaError): ...
class DocstringParseError(GlossaError): ...
class FixConflictError(GlossaError): ...
class ValidationError(GlossaError): ...
class FileWriteError(GlossaError): ...
class PluginLoadError(GlossaError): ...
```

## Failure Semantics

- **Configuration and bootstrap failures** are fatal and stop the run immediately.
- **Per-file extraction or parse failures** are non-fatal by default. Glossa records
  an operational error for that file, continues processing other files, and returns a
  partial-failure exit code.
- **Rule execution failures** are treated as bugs and surfaced as operational errors.
- **Fix validation failures** leave the original file unchanged.

Malformed docstrings that can still be lexed become `ParseIssue` values and may also
trigger diagnostics. Only unrecoverable parser failures become `DocstringParseError`.

## Exit Codes

| Exit Code | Meaning |
| --------- | ------- |
| `0` | Run completed successfully and found no diagnostics / no pending fixes |
| `1` | Run completed successfully and found diagnostics / available fixes |
| `2` | Usage or configuration error |
| `3` | Fatal operational error before analysis could complete |
| `4` | Partial failure: some files analyzed, some files failed operationally |
