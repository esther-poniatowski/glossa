# Testing Strategy

Testing follows the layer boundaries and directly targets the risky rules.

## Domain Tests

- parser unit tests over raw docstring strings
- lossless round-trip tests for quote style, indentation, and section ordering
- rule tests over pure `LintTarget` fixtures with no I/O
- heuristic corpus tests for non-imperative-summary mood detection
- confidence-threshold tests for missing-raises-section and missing-warns-section fact handling

## Application Tests

- target assembly tests for related entities such as class + `__init__`
- policy resolution tests for per-file overrides and inline suppressions
- fix conflict detection tests
- fix idempotency tests: applying the same accepted fix twice yields identical output
- fix validation tests: edited output reparses and reruns cleanly for affected rules

## Infrastructure Tests

- extraction tests for modules, classes, nested classes, properties, generators,
  decorators, overloads, `*args`, and `**kwargs`
- config loader tests for both file formats
- plugin loader contract tests

## Adapter Tests

- CLI end-to-end tests for `lint`, `fix`, and `check`
- exit-code tests for clean, diagnostic, fatal, and partial-failure runs
- formatter tests for text and JSON output

## Required Edge-Case Matrix

The test suite must include explicit coverage for:

- empty files
- comments-only files
- files with syntax errors
- malformed docstrings
- nested classes
- overloaded functions
- generators
- properties with short declarative summaries
- rich property docstrings with `Returns` / `Raises`
- decorators that preserve signatures
- decorators that obscure signatures
- `*args` / `**kwargs`
- duplicate sections
- unknown sections
- overlapping fix plans
