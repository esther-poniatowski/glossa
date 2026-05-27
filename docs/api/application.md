<a id="application"></a>

# Application

Application layer orchestrating linting and fixing workflows.

<a id="module-glossa.application.protocols"></a>

<a id="protocols"></a>

## Protocols

Ports (Protocol classes) that infrastructure adapters must satisfy.

Each protocol in this module represents a dependency boundary: the application
layer declares *what* it needs; infrastructure layers provide conforming
implementations without the application importing them directly.

<a id="glossa.application.protocols.RuleProvider"></a>

### *class* glossa.application.protocols.RuleProvider(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Supplies a collection of lint rules.

Implemented by third-party plugins that register rules for glossa to
discover via entry points.

<a id="glossa.application.protocols.RuleProvider.load_rules"></a>

#### load_rules()

Return all rules provided by this plugin.

* **Returns:**
  Tuple of rule objects contributed by this provider.
* **Return type:**
  [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[Rule](domain-rules.md#glossa.domain.rules.Rule), …]

<a id="glossa.application.protocols.DiscoveryPort"></a>

### *class* glossa.application.protocols.DiscoveryPort(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Discovers Python source files under a set of root paths.

Implementations are responsible for recursing into directories,
filtering by file extension, and honouring any exclusion patterns.

<a id="glossa.application.protocols.DiscoveryPort.discover"></a>

#### discover(paths, exclude=())

Yield project-relative POSIX path strings for Python source files.

* **Parameters:**
  * **paths** (*Sequence* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *]*) – Root paths (files or directories) to search.
  * **exclude** (*Sequence* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *]* *,* *optional*) – Glob patterns for paths that should be skipped.
* **Yields:**
  *str* – Project-relative POSIX path string for each discovered Python
  source file.

<a id="glossa.application.protocols.ExtractionPort"></a>

### *class* glossa.application.protocols.ExtractionPort(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Extracts lintable targets from a Python source file.

Implementations parse the source text and produce a flat sequence of
`ExtractedTarget` objects, one per documentable symbol.

<a id="glossa.application.protocols.ExtractionPort.extract"></a>

#### extract(source_id, source_text)

Parse a Python source file and return extracted targets.

* **Parameters:**
  * **source_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Project-relative POSIX path that uniquely identifies the source
    file (used to populate `SourceRef` values inside the results).
  * **source_text** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Full text content of the source file.
* **Returns:**
  One `ExtractedTarget` per documentable symbol found in the
  source file.
* **Return type:**
  [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[ExtractedTarget](domain-contracts.md#glossa.domain.contracts.extraction.ExtractedTarget), …]

<a id="glossa.application.protocols.FilePort"></a>

### *class* glossa.application.protocols.FilePort(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Reads and writes source file content.

Implementations handle the I/O mechanics (encoding, path resolution,
atomic writes, etc.) so that the application layer stays pure.

<a id="glossa.application.protocols.FilePort.read"></a>

#### read(source_id)

Return the text content of a source file.

* **Parameters:**
  **source_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Project-relative POSIX path identifying the file to read.
* **Returns:**
  Full decoded text content of the file.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="glossa.application.protocols.FilePort.write"></a>

#### write(source_id, content)

Write content to a source file.

* **Parameters:**
  * **source_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Project-relative POSIX path identifying the file to write.
  * **content** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Text content to write to the file.

<a id="glossa.application.protocols.ConfigPort"></a>

### *class* glossa.application.protocols.ConfigPort(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Loads raw configuration data for glossa.

Implementations locate and parse `pyproject.toml` (`[tool.glossa]`
section) or `.glossa.yaml`, returning an unvalidated dictionary that
the application layer can then map onto `GlossaConfig`.

<a id="glossa.application.protocols.ConfigPort.load"></a>

#### load(config_path=None)

Return raw configuration dictionary.

* **Parameters:**
  **config_path** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None* *,* *optional*) – Explicit path to a configuration file.  When `None`,
  implementations should search for `pyproject.toml` or
  `.glossa.yaml` starting from the current working directory.
* **Returns:**
  Raw, unvalidated configuration data.  An empty dict is returned
  when no configuration file is found.
* **Return type:**
  [dict](https://docs.python.org/3/library/stdtypes.html#dict)[[str](https://docs.python.org/3/library/stdtypes.html#str), [object](https://docs.python.org/3/library/functions.html#object)]

<a id="glossa.application.protocols.PluginPort"></a>

### *class* glossa.application.protocols.PluginPort(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Discovers and loads third-party rule providers.

Implementations use Python entry points (or an equivalent mechanism) to
find installed packages that advertise glossa rule providers.

<a id="glossa.application.protocols.PluginPort.load_plugins"></a>

#### load_plugins()

Return rule providers discovered via entry points.

* **Returns:**
  One `RuleProvider` instance per registered plugin.  Returns an
  empty tuple when no plugins are installed.
* **Return type:**
  [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[RuleProvider](#glossa.application.protocols.RuleProvider), …]

<a id="module-glossa.application.service"></a>

<a id="service"></a>

## Service

Application services for project-wide lint and fix runs.

<a id="glossa.application.service.OperationalIssue"></a>

### *class* glossa.application.service.OperationalIssue(source_id: 'str | None', message: 'str')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.service.OperationalIssue.source_id"></a>

#### source_id *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.application.service.OperationalIssue.message"></a>

#### message *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.application.service.LintRunResult"></a>

### *class* glossa.application.service.LintRunResult(files: 'tuple[AnalyzedFile, ...]', operational_issues: 'tuple[OperationalIssue, ...]', effective_config: 'GlossaConfig')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.service.LintRunResult.files"></a>

#### files *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[AnalyzedFile](#glossa.application.linting.AnalyzedFile), ...]*

<a id="glossa.application.service.LintRunResult.operational_issues"></a>

#### operational_issues *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[OperationalIssue](#glossa.application.service.OperationalIssue), ...]*

<a id="glossa.application.service.LintRunResult.effective_config"></a>

#### effective_config *: [GlossaConfig](#glossa.application.configuration.GlossaConfig)*

<a id="glossa.application.service.LintRunResult.diagnostics"></a>

#### *property* diagnostics *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[Diagnostic](domain-contracts.md#glossa.domain.contracts.evaluation.Diagnostic), ...]*

<a id="glossa.application.service.FixRunResult"></a>

### *class* glossa.application.service.FixRunResult(results: 'tuple[FixResult, ...]', fixable_diagnostics: 'tuple[Diagnostic, ...]', operational_issues: 'tuple[OperationalIssue, ...]', fix_enabled: 'bool')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.service.FixRunResult.results"></a>

#### results *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[FixResult](#glossa.application.fixing.FixResult), ...]*

<a id="glossa.application.service.FixRunResult.fixable_diagnostics"></a>

#### fixable_diagnostics *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[Diagnostic](domain-contracts.md#glossa.domain.contracts.evaluation.Diagnostic), ...]*

<a id="glossa.application.service.FixRunResult.operational_issues"></a>

#### operational_issues *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[OperationalIssue](#glossa.application.service.OperationalIssue), ...]*

<a id="glossa.application.service.FixRunResult.fix_enabled"></a>

#### fix_enabled *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.application.service.FixRunResult.applied_count"></a>

#### *property* applied_count *: [int](https://docs.python.org/3/library/functions.html#int)*

<a id="glossa.application.service.FixRunResult.rejected_count"></a>

#### *property* rejected_count *: [int](https://docs.python.org/3/library/functions.html#int)*

<a id="glossa.application.service.CheckRunResult"></a>

### *class* glossa.application.service.CheckRunResult(fixable_count: 'int', operational_issues: 'tuple[OperationalIssue, ...]')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.service.CheckRunResult.fixable_count"></a>

#### fixable_count *: [int](https://docs.python.org/3/library/functions.html#int)*

<a id="glossa.application.service.CheckRunResult.operational_issues"></a>

#### operational_issues *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[OperationalIssue](#glossa.application.service.OperationalIssue), ...]*

<a id="glossa.application.service.GlossaService"></a>

### *class* glossa.application.service.GlossaService(\*, config, discovery, extractor, file_port, registry)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Facade exposing intent-level lint and fix workflows.

<a id="glossa.application.service.GlossaService.config"></a>

#### *property* config *: [GlossaConfig](#glossa.application.configuration.GlossaConfig)*

<a id="glossa.application.service.GlossaService.lint_paths"></a>

#### lint_paths(paths, \*, select=None, ignore=None, output_format=None, color=None)

<a id="glossa.application.service.GlossaService.fix_paths"></a>

#### fix_paths(paths, \*, dry_run=False, select=None, ignore=None)

<a id="glossa.application.service.GlossaService.check_paths"></a>

#### check_paths(paths, \*, select=None, ignore=None)

<a id="glossa.application.service.GlossaService.lint_source"></a>

#### lint_source(source_text, \*, source_id='_\_input_\_.py', select=None, ignore=None)

<a id="module-glossa.application.linting"></a>

<a id="linting"></a>

## Linting

Linting orchestration and analyzed-file assembly.

<a id="glossa.application.linting.AnalyzedTarget"></a>

### *class* glossa.application.linting.AnalyzedTarget(lint_target: 'LintTarget', diagnostics: 'tuple[Diagnostic, ...]')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.linting.AnalyzedTarget.lint_target"></a>

#### lint_target *: [LintTarget](domain-contracts.md#glossa.domain.contracts.evaluation.LintTarget)*

<a id="glossa.application.linting.AnalyzedTarget.diagnostics"></a>

#### diagnostics *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[Diagnostic](domain-contracts.md#glossa.domain.contracts.evaluation.Diagnostic), ...]*

<a id="glossa.application.linting.AnalyzedFile"></a>

### *class* glossa.application.linting.AnalyzedFile(source_id: 'str', source_text: 'str', targets: 'tuple[AnalyzedTarget, ...]')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.linting.AnalyzedFile.source_id"></a>

#### source_id *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.application.linting.AnalyzedFile.source_text"></a>

#### source_text *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.application.linting.AnalyzedFile.targets"></a>

#### targets *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[AnalyzedTarget](#glossa.application.linting.AnalyzedTarget), ...]*

<a id="glossa.application.linting.AnalyzedFile.diagnostics"></a>

#### *property* diagnostics *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[Diagnostic](domain-contracts.md#glossa.domain.contracts.evaluation.Diagnostic), ...]*

<a id="glossa.application.linting.analyze_file"></a>

### glossa.application.linting.analyze_file(source_id, source_text, extraction_port, config, registry)

Analyze a single Python source file and return structured results.

<a id="glossa.application.linting.assemble_lint_target"></a>

### glossa.application.linting.assemble_lint_target(extracted, parsed, related)

Map an extracted target into the pure lint target used by rules.

<a id="glossa.application.linting.find_analyzed_target"></a>

### glossa.application.linting.find_analyzed_target(analyzed_file, symbol_path)

Return the analyzed target for *symbol_path*, if present.

<a id="module-glossa.application.fixing"></a>

<a id="fixing"></a>

## Fixing

Source-level fix orchestration.

<a id="glossa.application.fixing.FixRejectionReason"></a>

### *class* glossa.application.fixing.FixRejectionReason(value, names=<not given>, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

<a id="glossa.application.fixing.FixRejectionReason.CONFLICT"></a>

#### CONFLICT *= 'conflict'*

<a id="glossa.application.fixing.FixRejectionReason.UNSUPPORTED"></a>

#### UNSUPPORTED *= 'unsupported'*

<a id="glossa.application.fixing.FixRejectionReason.VALIDATION_FAILED"></a>

#### VALIDATION_FAILED *= 'validation_failed'*

<a id="glossa.application.fixing.FixRejection"></a>

### *class* glossa.application.fixing.FixRejection(plan: 'FixPlan', reason: 'FixRejectionReason', details: 'str')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.fixing.FixRejection.plan"></a>

#### plan *: [FixPlan](domain-contracts.md#glossa.domain.contracts.evaluation.FixPlan)*

<a id="glossa.application.fixing.FixRejection.reason"></a>

#### reason *: [FixRejectionReason](#glossa.application.fixing.FixRejectionReason)*

<a id="glossa.application.fixing.FixRejection.details"></a>

#### details *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.application.fixing.FixTransformation"></a>

### *class* glossa.application.fixing.FixTransformation(source_id, accepted, rejected, edited_source)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Pure fix computation result: edited source and plan bookkeeping, no I/O.

<a id="glossa.application.fixing.FixTransformation.source_id"></a>

#### source_id *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.application.fixing.FixTransformation.accepted"></a>

#### accepted *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[FixPlan](domain-contracts.md#glossa.domain.contracts.evaluation.FixPlan), ...]*

<a id="glossa.application.fixing.FixTransformation.rejected"></a>

#### rejected *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[FixRejection](#glossa.application.fixing.FixRejection), ...]*

<a id="glossa.application.fixing.FixTransformation.edited_source"></a>

#### edited_source *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.application.fixing.FixResult"></a>

### *class* glossa.application.fixing.FixResult(source_id: 'str', applied: 'tuple[FixPlan, ...]', rejected: 'tuple[FixRejection, ...]', validation_passed: 'bool')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.fixing.FixResult.source_id"></a>

#### source_id *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.application.fixing.FixResult.applied"></a>

#### applied *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[FixPlan](domain-contracts.md#glossa.domain.contracts.evaluation.FixPlan), ...]*

<a id="glossa.application.fixing.FixResult.rejected"></a>

#### rejected *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[FixRejection](#glossa.application.fixing.FixRejection), ...]*

<a id="glossa.application.fixing.FixResult.validation_passed"></a>

#### validation_passed *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.application.fixing.apply_fixes"></a>

### glossa.application.fixing.apply_fixes(analyzed_files, config)

Compute source-level fixes for analyzed files without applying or validating them.

<a id="module-glossa.application.configuration"></a>

<a id="configuration"></a>

## Configuration

Typed configuration models and validation.

<a id="glossa.application.configuration.OutputFormat"></a>

### *class* glossa.application.configuration.OutputFormat(value, names=<not given>, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

<a id="glossa.application.configuration.OutputFormat.TEXT"></a>

#### TEXT *= 'text'*

<a id="glossa.application.configuration.OutputFormat.JSON"></a>

#### JSON *= 'json'*

<a id="glossa.application.configuration.FixApplyMode"></a>

### *class* glossa.application.configuration.FixApplyMode(value, names=<not given>, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

<a id="glossa.application.configuration.FixApplyMode.NEVER"></a>

#### NEVER *= 'never'*

<a id="glossa.application.configuration.FixApplyMode.SAFE"></a>

#### SAFE *= 'safe'*

<a id="glossa.application.configuration.FixApplyMode.UNSAFE"></a>

#### UNSAFE *= 'unsafe'*

<a id="glossa.application.configuration.RuleSelection"></a>

### *class* glossa.application.configuration.RuleSelection(select: 'tuple[str, ...]', ignore: 'tuple[str, ...]', severity_overrides: 'Mapping[str, Severity]', per_file_ignores: 'Mapping[str, tuple[str, ...]]', rule_options: 'Mapping[str, Mapping[str, object]]', section_order: 'tuple[str, ...]')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.configuration.RuleSelection.select"></a>

#### select *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.application.configuration.RuleSelection.ignore"></a>

#### ignore *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.application.configuration.RuleSelection.severity_overrides"></a>

#### severity_overrides *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/library/stdtypes.html#str), [Severity](domain-contracts.md#glossa.domain.contracts.core.Severity)]*

<a id="glossa.application.configuration.RuleSelection.per_file_ignores"></a>

#### per_file_ignores *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/library/stdtypes.html#str), [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]]*

<a id="glossa.application.configuration.RuleSelection.rule_options"></a>

#### rule_options *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/library/stdtypes.html#str), [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/library/stdtypes.html#str), [object](https://docs.python.org/3/library/functions.html#object)]]*

<a id="glossa.application.configuration.RuleSelection.section_order"></a>

#### section_order *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.application.configuration.SuppressionPolicy"></a>

### *class* glossa.application.configuration.SuppressionPolicy(inline_enabled: 'bool', directive_prefix: 'str')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.configuration.SuppressionPolicy.inline_enabled"></a>

#### inline_enabled *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.application.configuration.SuppressionPolicy.directive_prefix"></a>

#### directive_prefix *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.application.configuration.FixPolicy"></a>

### *class* glossa.application.configuration.FixPolicy(enabled: 'bool', apply: 'FixApplyMode', validate_after_apply: 'bool')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.configuration.FixPolicy.enabled"></a>

#### enabled *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.application.configuration.FixPolicy.apply"></a>

#### apply *: [FixApplyMode](#glossa.application.configuration.FixApplyMode)*

<a id="glossa.application.configuration.FixPolicy.validate_after_apply"></a>

#### validate_after_apply *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.application.configuration.OutputOptions"></a>

### *class* glossa.application.configuration.OutputOptions(format: 'OutputFormat', color: 'bool', show_source: 'bool')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.configuration.OutputOptions.format"></a>

#### format *: [OutputFormat](#glossa.application.configuration.OutputFormat)*

<a id="glossa.application.configuration.OutputOptions.color"></a>

#### color *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.application.configuration.OutputOptions.show_source"></a>

#### show_source *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.application.configuration.ParsingOptions"></a>

### *class* glossa.application.configuration.ParsingOptions(section_aliases: 'Mapping[str, str]')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.configuration.ParsingOptions.section_aliases"></a>

#### section_aliases *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/library/stdtypes.html#str), [str](https://docs.python.org/3/library/stdtypes.html#str)]*

<a id="glossa.application.configuration.GlossaConfig"></a>

### *class* glossa.application.configuration.GlossaConfig(rules: 'RuleSelection', suppressions: 'SuppressionPolicy', fix: 'FixPolicy', output: 'OutputOptions', parsing: 'ParsingOptions')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.configuration.GlossaConfig.rules"></a>

#### rules *: [RuleSelection](#glossa.application.configuration.RuleSelection)*

<a id="glossa.application.configuration.GlossaConfig.suppressions"></a>

#### suppressions *: [SuppressionPolicy](#glossa.application.configuration.SuppressionPolicy)*

<a id="glossa.application.configuration.GlossaConfig.fix"></a>

#### fix *: [FixPolicy](#glossa.application.configuration.FixPolicy)*

<a id="glossa.application.configuration.GlossaConfig.output"></a>

#### output *: [OutputOptions](#glossa.application.configuration.OutputOptions)*

<a id="glossa.application.configuration.GlossaConfig.parsing"></a>

#### parsing *: [ParsingOptions](#glossa.application.configuration.ParsingOptions)*

<a id="glossa.application.configuration.resolve_config"></a>

### glossa.application.configuration.resolve_config(raw)

Validate a raw config mapping and return typed configuration.

<a id="glossa.application.configuration.config_with_overrides"></a>

### glossa.application.configuration.config_with_overrides(config, \*, select=None, ignore=None, output_format=None, color=None)

Return a copy of *config* with CLI-style overrides applied.

<a id="module-glossa.application.policy"></a>

<a id="policy"></a>

## Policy

Rule selection, per-file overrides, and inline suppressions.

<a id="glossa.application.policy.matches_rule"></a>

### glossa.application.policy.matches_rule(rule_metadata, pattern)

Return True if *pattern* matches the rule’s name or group.

<a id="glossa.application.policy.matches_file_pattern"></a>

### glossa.application.policy.matches_file_pattern(source_id, glob_pattern)

Return True if source_id matches glob_pattern using fnmatch.

<a id="glossa.application.policy.resolve_rule_policy"></a>

### glossa.application.policy.resolve_rule_policy(rule_metadata, source_id, config)

Resolve whether a rule is enabled for a given source file.

<a id="resolution-order"></a>

### Resolution order

1. A rule in `config.rules.ignore` is always disabled.
2. A rule matching any pattern in `config.rules.select` is enabled.
3. `config.rules.per_file_ignores`: if source_id matches a glob pattern
   whose rule list includes the rule name or group, the rule is disabled.
4. Severity is taken from `config.rules.severity_overrides` when present,
   otherwise from the rule’s `default_severity`.
5. Options are merged from the rule’s `option_schema` defaults with any
   user-supplied overrides in `config.rules.rule_options`.

<a id="glossa.application.policy.parse_inline_suppression"></a>

### glossa.application.policy.parse_inline_suppression(line, directive_prefix='glossa: ignore=')

Parse an inline suppression comment from a source line.

### Examples

```pycon
>>> parse_inline_suppression('x = 1  # glossa: ignore=missing-period,first-person-voice')
('missing-period', 'first-person-voice')
>>> parse_inline_suppression('x = 1  # some other comment') is None
True
```

<a id="glossa.application.policy.is_rule_suppressed"></a>

### glossa.application.policy.is_rule_suppressed(rule_name, suppressions)

Return True if rule_name is present in the suppressions tuple.

<a id="module-glossa.application.registry"></a>

<a id="registry"></a>

## Registry

Rule registry and plugin loading orchestration.

<a id="glossa.application.registry.RuleRegistry"></a>

### *class* glossa.application.registry.RuleRegistry(builtins: 'tuple[Rule, ...]', plugins: 'tuple[Rule, ...]')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.application.registry.RuleRegistry.builtins"></a>

#### builtins *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[Rule](domain-rules.md#glossa.domain.rules.Rule), ...]*

<a id="glossa.application.registry.RuleRegistry.plugins"></a>

#### plugins *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[Rule](domain-rules.md#glossa.domain.rules.Rule), ...]*

<a id="glossa.application.registry.RuleRegistry.all_rules"></a>

#### all_rules()

<a id="glossa.application.registry.build_builtin_registry"></a>

### glossa.application.registry.build_builtin_registry()

Instantiate all built-in rule classes and return a populated RuleRegistry.

Imports rule classes from each sub-module under `glossa.domain.rules`,
instantiates each one, and bundles them into a [`RuleRegistry`](#glossa.application.registry.RuleRegistry) with
an empty plugins tuple.

* **Returns:**
  A registry containing all built-in rules and no plugin rules.
* **Return type:**
  [RuleRegistry](#glossa.application.registry.RuleRegistry)
