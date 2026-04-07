# Rule Reference

Complete reference for all glossa lint rules. Rules are organized into groups that
reflect the aspect of docstring quality they target. Rule names follow the pattern
`<descriptive-slug>`, and rules can be selected or ignored individually or by group
name (e.g., `presence`, `prose`, `structure`).

## Presence and Coverage (`presence`)

| Rule | Description | Applies To | Fixable |
| ---- | ----------- | ---------- | ------- |
| missing-module-docstring | Missing public module docstring | module | No |
| missing-class-docstring | Missing public class docstring | class | No |
| missing-callable-docstring | Missing public callable docstring | function, method, property | No |
| missing-parameters-section | Missing Parameters section for documentable parameters | function, method, class | Yes |
| missing-returns-section | Missing Returns section where required | function, method, property | Yes |
| missing-yields-section | Missing Yields section for generators | function, method, property | Yes |
| missing-raises-section | Missing Raises section for public-contract exceptions | function, method, property | No |
| missing-warns-section | Missing Warns section for public warnings | function, method, property | No |
| missing-module-inventory | Missing module Classes/Functions inventory when required | module | Yes |
| missing-attributes-section | Missing Attributes section where class attributes need docs | class | No |
| params-in-init-not-class | Constructor parameters documented in __init__ instead of class | class | No |
| missing-deprecation-directive | Missing deprecation directive for deprecated public API | all | No |

## Prose and Summary Format (`prose`)

| Rule | Description | Applies To | Fixable |
| ---- | ----------- | ---------- | ------- |
| non-imperative-summary | Summary not imperative where required | function, method, property | No |
| missing-period | Summary line missing terminal period | all | Yes |
| missing-blank-after-summary | Missing blank line after summary when body follows | all | Yes |
| first-person-voice | First-person voice in docstring | all | No |
| second-person-voice | Second-person voice in docstring | all | No |
| markdown-in-docstring | Markdown syntax where RST is required | all | No |

`non-imperative-summary` applies only to callables (function, method, property), not
to modules or classes.

## Section Structure and Placement (`structure`)

| Rule | Description | Applies To | Fixable |
| ---- | ----------- | ---------- | ------- |
| malformed-underline | Section underline is malformed | all | Yes |
| section-order | Section order violates NumPy policy | all | No |
| undocumented-parameter | Parameter in signature but missing from docstring | function, method, class | Yes |
| extraneous-parameter | Parameter in docstring but not in signature | function, method, class | No |
| malformed-deprecation | Deprecation directive malformed or misplaced | all | No |
| rst-directive-instead-of-section | RST directive used where NumPy section exists | all | No |
| examples-in-non-entry-module | Examples in non-entry-point module (suppressed by default) | module | No |

## Typed Entry Consistency (`typed-entries`)

| Rule | Description | Applies To | Fixable |
| ---- | ----------- | ---------- | ------- |
| missing-param-type | Parameter type missing from docstring | function, method, class | Yes |
| param-type-mismatch | Parameter type mismatches annotation | function, method, class | Yes |
| missing-return-type | Return type missing from docstring | function, method, property | Yes |
| return-type-mismatch | Return type mismatches annotation | function, method, property | Yes |
| yield-type-mismatch | Yield type missing or mismatched | function, method, property | Yes |
| missing-attribute-type | Attribute type missing | class | Yes |

## Anti-Patterns (`anti-patterns`)

| Rule | Description | Applies To | Fixable |
| ---- | ----------- | ---------- | ------- |
| empty-docstring | Empty docstring body | all | No |
| trivial-dunder-docstring | Trivial dunder method docstring | method | No |
| redundant-returns-none | Redundant Returns None section | function, method, property | Yes |
| rst-note-warning-directive | RST note/warning directive instead of NumPy section | all | No |

## Non-Goals

The docstring guide contains conventions that are valuable but not reliably enforceable
by a static docstring linter. Glossa v1 explicitly does **not** attempt to:

- lint inline comments outside docstrings (guide section 6)
- judge semantic quality of prose beyond rule-specific heuristics
- execute doctest examples
- infer optional `See Also` links from API topology
- reason about behavior introduced only at runtime by dynamic decorators or metaclasses
