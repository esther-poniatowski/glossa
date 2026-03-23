# Configuration

This guide documents the target configuration model defined in the
[Design Plan](../design-plan.md). The current codebase may implement it incrementally.

## Sources and Precedence

Configuration is resolved in the following order, from lowest to highest precedence:

1. Built-in defaults
2. `pyproject.toml` or `.glossa.yaml`
3. Per-file overrides
4. Inline suppressions
5. CLI flags

## `pyproject.toml`

```toml
[tool.glossa.rules]
select = ["D1xx", "D2xx", "D3xx", "D4xx", "D5xx"]
ignore = ["D205"]

[tool.glossa.rules.severity_overrides]
D201 = "error"

[tool.glossa.rules.per_file_ignores]
"tests/**.py" = ["D102"]

[tool.glossa.rules.rule_options.D104]
simple_property_requires_returns = false

[tool.glossa.rules.rule_options.D108]
inventory_threshold = 2

[tool.glossa.suppressions]
inline_enabled = true
directive_prefix = "glossa: ignore="

[tool.glossa.fix]
enabled = true
apply = "safe"
validate_after_apply = true

[tool.glossa.output]
format = "text"
color = true
show_source = true
```

## `.glossa.yaml`

```yaml
rules:
  select: ["D1xx", "D2xx", "D3xx", "D4xx", "D5xx"]
  ignore: ["D205"]
  severity_overrides:
    D201: error
  per_file_ignores:
    "tests/**.py": ["D102"]
  rule_options:
    D104:
      simple_property_requires_returns: false
    D108:
      inventory_threshold: 2

suppressions:
  inline_enabled: true
  directive_prefix: "glossa: ignore="

fix:
  enabled: true
  apply: safe
  validate_after_apply: true

output:
  format: text
  color: true
  show_source: true
```

## Inline Suppressions

Inline suppressions are attached to a module header or target definition:

```python
def render(config: Config) -> str:  # glossa: ignore=D200,D205
    """Returns the rendered text"""
```

## Key Concepts

- `rules.select` and `rules.ignore` control which rules are active.
- `severity_overrides` changes the diagnostic level of specific rules.
- `per_file_ignores` disables rules for matching file globs.
- `rule_options` turns ambiguous guide language into explicit policy.
- `fix.apply` distinguishes disabled fixes, validated safe fixes, and explicitly unsafe modes.
