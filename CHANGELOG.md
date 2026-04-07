# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Descriptive rule names replace numeric codes as the sole rule identifier. Rules are
  identified by readable kebab-case names (e.g. `missing-period`,
  `undocumented-parameter`) and organized into groups (`presence`, `prose`, `structure`,
  `typed-entries`, `anti-patterns`).
- Group-based rule selection: `--select presence,prose` or in config
  `select = ["presence", "prose"]`.
- `Usage` recognized as a built-in prose section, placed between Attributes and Notes in
  the default section order.
- `Arguments` and `Args` recognized as aliases for the `Parameters` section header.
- Configurable section aliases via `[tool.glossa.parsing.section_aliases]` to map custom
  section titles to known kinds.
- Support for linting external projects via absolute paths.
- `RuleMetadata` now has `name` (descriptive identifier) and `group` (category) fields.

### Changed

- `Diagnostic.rule` replaces `Diagnostic.code` as the diagnostic identifier field.
- `ParseIssue.kind` replaces `ParseIssue.code`.
- Rule classes renamed from numeric convention (D100) to descriptive PascalCase
  (MissingModuleDocstring).
- `non-imperative-summary` rule now applies only to callables (function, method,
  property), not classes or modules. NumPy style permits noun phrases for class
  docstrings.
- `first-person-voice` and `second-person-voice` rules now skip code blocks (interactive
  prompts, RST code-block directives) to avoid false positives on identifiers.
- `missing-blank-after-summary` rule now checks relative to the parsed summary span,
  preventing false positives on docstrings with leading reST title headers.
- Summary extraction skips leading reST title+underline headers (e.g.
  `module.name\n==========`).
- Default `rules.ignore` now includes `examples-in-non-entry-module`.
- CLI `--select` and `--ignore` accept rule names and group names instead of numeric
  codes.
- Default path fallback extracted to `DEFAULT_PATHS` constant.

### Removed

- Numeric rule codes (D100, D201, etc.) — no longer recognized in any context.
- `create_linter()` backward-compatible alias — use `bootstrap()` directly.
- `SectionParser` class and `extra_parsers` parameter from the public parsing API.

### Fixed

- CLI crash from Typer/Click incompatibility with variadic argument defaults.
- `FileDiscovery` and `LocalFilePort` failing on absolute paths outside the project
  tree.
- Rich markup collision in `fix --dry-run` output when source paths contain brackets.
