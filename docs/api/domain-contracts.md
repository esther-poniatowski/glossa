<a id="domain-contracts"></a>

# Domain Contracts

Cross-layer DTOs shared across Glossa. Owned by the domain layer; constructed by infrastructure, orchestrated by the application, and consumed by domain rules.

<a id="module-glossa.domain.contracts.core"></a>

<a id="core"></a>

## Core

Foundational identification, classification, and severity types.

<a id="glossa.domain.contracts.core.SourceRef"></a>

### *class* glossa.domain.contracts.core.SourceRef(source_id: 'str', symbol_path: 'tuple[str, ...]')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.core.SourceRef.source_id"></a>

#### source_id *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.core.SourceRef.symbol_path"></a>

#### symbol_path *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.contracts.core.TextPosition"></a>

### *class* glossa.domain.contracts.core.TextPosition(line: 'int', column: 'int')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.core.TextPosition.line"></a>

#### line *: [int](https://docs.python.org/3/library/functions.html#int)*

<a id="glossa.domain.contracts.core.TextPosition.column"></a>

#### column *: [int](https://docs.python.org/3/library/functions.html#int)*

<a id="glossa.domain.contracts.core.TextSpan"></a>

### *class* glossa.domain.contracts.core.TextSpan(start: 'TextPosition', end: 'TextPosition')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.core.TextSpan.start"></a>

#### start *: [TextPosition](#glossa.domain.contracts.core.TextPosition)*

<a id="glossa.domain.contracts.core.TextSpan.end"></a>

#### end *: [TextPosition](#glossa.domain.contracts.core.TextPosition)*

<a id="glossa.domain.contracts.core.TargetKind"></a>

### *class* glossa.domain.contracts.core.TargetKind(value, names=<not given>, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

<a id="glossa.domain.contracts.core.TargetKind.MODULE"></a>

#### MODULE *= 'module'*

<a id="glossa.domain.contracts.core.TargetKind.CLASS"></a>

#### CLASS *= 'class'*

<a id="glossa.domain.contracts.core.TargetKind.FUNCTION"></a>

#### FUNCTION *= 'function'*

<a id="glossa.domain.contracts.core.TargetKind.METHOD"></a>

#### METHOD *= 'method'*

<a id="glossa.domain.contracts.core.TargetKind.PROPERTY"></a>

#### PROPERTY *= 'property'*

<a id="glossa.domain.contracts.core.Visibility"></a>

### *class* glossa.domain.contracts.core.Visibility(value, names=<not given>, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

<a id="glossa.domain.contracts.core.Visibility.PUBLIC"></a>

#### PUBLIC *= 'public'*

<a id="glossa.domain.contracts.core.Visibility.INTERNAL"></a>

#### INTERNAL *= 'internal'*

<a id="glossa.domain.contracts.core.Visibility.PRIVATE"></a>

#### PRIVATE *= 'private'*

<a id="glossa.domain.contracts.core.Severity"></a>

### *class* glossa.domain.contracts.core.Severity(value, names=<not given>, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

<a id="glossa.domain.contracts.core.Severity.ERROR"></a>

#### ERROR *= 'error'*

<a id="glossa.domain.contracts.core.Severity.WARNING"></a>

#### WARNING *= 'warning'*

<a id="glossa.domain.contracts.core.Severity.CONVENTION"></a>

#### CONVENTION *= 'convention'*

<a id="module-glossa.domain.contracts.extraction"></a>

<a id="extraction"></a>

## Extraction

DTOs produced by infrastructure extraction and consumed by the application layer.

<a id="glossa.domain.contracts.extraction.Confidence"></a>

### *class* glossa.domain.contracts.extraction.Confidence(value, names=<not given>, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

<a id="glossa.domain.contracts.extraction.Confidence.HIGH"></a>

#### HIGH *= 'high'*

<a id="glossa.domain.contracts.extraction.Confidence.MEDIUM"></a>

#### MEDIUM *= 'medium'*

<a id="glossa.domain.contracts.extraction.Confidence.LOW"></a>

#### LOW *= 'low'*

<a id="glossa.domain.contracts.extraction.ExceptionEvidence"></a>

### *class* glossa.domain.contracts.extraction.ExceptionEvidence(value, names=<not given>, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

<a id="glossa.domain.contracts.extraction.ExceptionEvidence.RAISE"></a>

#### RAISE *= 'raise'*

<a id="glossa.domain.contracts.extraction.ExceptionEvidence.RERAISE"></a>

#### RERAISE *= 'reraise'*

<a id="glossa.domain.contracts.extraction.ExceptionEvidence.DOCUMENTED_CONTRACT"></a>

#### DOCUMENTED_CONTRACT *= 'documented_contract'*

<a id="glossa.domain.contracts.extraction.ExtractedDocstring"></a>

### *class* glossa.domain.contracts.extraction.ExtractedDocstring(body: 'str', quote: 'Literal[\\'"""\\', "\\'\\'\\'"]', string_prefix: 'str', indentation: 'str', body_span: 'TextSpan', literal_span: 'TextSpan')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.extraction.ExtractedDocstring.body"></a>

#### body *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.extraction.ExtractedDocstring.quote"></a>

#### quote *: [Literal](https://docs.python.org/3/library/typing.html#typing.Literal)['"""', "'''"]*

<a id="glossa.domain.contracts.extraction.ExtractedDocstring.string_prefix"></a>

#### string_prefix *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.extraction.ExtractedDocstring.indentation"></a>

#### indentation *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.extraction.ExtractedDocstring.body_span"></a>

#### body_span *: [TextSpan](#glossa.domain.contracts.core.TextSpan)*

<a id="glossa.domain.contracts.extraction.ExtractedDocstring.literal_span"></a>

#### literal_span *: [TextSpan](#glossa.domain.contracts.core.TextSpan)*

<a id="glossa.domain.contracts.extraction.ParameterFact"></a>

### *class* glossa.domain.contracts.extraction.ParameterFact(name: 'str', annotation: 'str | None', default: 'str | None', kind: "Literal['positional_only', 'positional_or_keyword', 'var_positional', 'keyword_only', 'var_keyword']")

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.extraction.ParameterFact.name"></a>

#### name *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.extraction.ParameterFact.annotation"></a>

#### annotation *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.extraction.ParameterFact.default"></a>

#### default *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.extraction.ParameterFact.kind"></a>

#### kind *: [Literal](https://docs.python.org/3/library/typing.html#typing.Literal)['positional_only', 'positional_or_keyword', 'var_positional', 'keyword_only', 'var_keyword']*

<a id="glossa.domain.contracts.extraction.SignatureFacts"></a>

### *class* glossa.domain.contracts.extraction.SignatureFacts(parameters: 'tuple[ParameterFact, ...]', return_annotation: 'str | None', returns_value: 'bool', yields_value: 'bool')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.extraction.SignatureFacts.parameters"></a>

#### parameters *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[ParameterFact](#glossa.domain.contracts.extraction.ParameterFact), ...]*

<a id="glossa.domain.contracts.extraction.SignatureFacts.return_annotation"></a>

#### return_annotation *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.extraction.SignatureFacts.returns_value"></a>

#### returns_value *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.domain.contracts.extraction.SignatureFacts.yields_value"></a>

#### yields_value *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.domain.contracts.extraction.ExceptionFact"></a>

### *class* glossa.domain.contracts.extraction.ExceptionFact(type_name: 'str', evidence: 'ExceptionEvidence', confidence: 'Confidence')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.extraction.ExceptionFact.type_name"></a>

#### type_name *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.extraction.ExceptionFact.evidence"></a>

#### evidence *: [ExceptionEvidence](#glossa.domain.contracts.extraction.ExceptionEvidence)*

<a id="glossa.domain.contracts.extraction.ExceptionFact.confidence"></a>

#### confidence *: [Confidence](#glossa.domain.contracts.extraction.Confidence)*

<a id="glossa.domain.contracts.extraction.WarningFact"></a>

### *class* glossa.domain.contracts.extraction.WarningFact(type_name: 'str', confidence: 'Confidence')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.extraction.WarningFact.type_name"></a>

#### type_name *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.extraction.WarningFact.confidence"></a>

#### confidence *: [Confidence](#glossa.domain.contracts.extraction.Confidence)*

<a id="glossa.domain.contracts.extraction.AttributeFact"></a>

### *class* glossa.domain.contracts.extraction.AttributeFact(name: 'str', annotation: 'str | None', defined_in_init: 'bool', is_public: 'bool')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.extraction.AttributeFact.name"></a>

#### name *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.extraction.AttributeFact.annotation"></a>

#### annotation *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.extraction.AttributeFact.defined_in_init"></a>

#### defined_in_init *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.domain.contracts.extraction.AttributeFact.is_public"></a>

#### is_public *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.domain.contracts.extraction.ModuleSymbolFact"></a>

### *class* glossa.domain.contracts.extraction.ModuleSymbolFact(name: 'str', kind: "Literal['class', 'function']", is_public: 'bool')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.extraction.ModuleSymbolFact.name"></a>

#### name *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.extraction.ModuleSymbolFact.kind"></a>

#### kind *: [Literal](https://docs.python.org/3/library/typing.html#typing.Literal)['class', 'function']*

<a id="glossa.domain.contracts.extraction.ModuleSymbolFact.is_public"></a>

#### is_public *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.domain.contracts.extraction.RelatedTargets"></a>

### *class* glossa.domain.contracts.extraction.RelatedTargets(parent: 'SourceRef | None' = None, constructor: 'SourceRef | None' = None, property_getter: 'SourceRef | None' = None)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.extraction.RelatedTargets.parent"></a>

#### parent *: [SourceRef](#glossa.domain.contracts.core.SourceRef) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

<a id="glossa.domain.contracts.extraction.RelatedTargets.constructor"></a>

#### constructor *: [SourceRef](#glossa.domain.contracts.core.SourceRef) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

<a id="glossa.domain.contracts.extraction.RelatedTargets.property_getter"></a>

#### property_getter *: [SourceRef](#glossa.domain.contracts.core.SourceRef) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

<a id="glossa.domain.contracts.extraction.ExtractedTarget"></a>

### *class* glossa.domain.contracts.extraction.ExtractedTarget(ref: 'SourceRef', kind: 'TargetKind', visibility: 'Visibility', is_test_target: 'bool', docstring: 'ExtractedDocstring | None', signature: 'SignatureFacts | None', exceptions: 'tuple[ExceptionFact, ...]', warnings: 'tuple[WarningFact, ...]', attributes: 'tuple[AttributeFact, ...]', module_symbols: 'tuple[ModuleSymbolFact, ...]', decorators: 'tuple[str, ...]', related: 'RelatedTargets', suppression_lines: 'tuple[str, ...]' = ())

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.extraction.ExtractedTarget.ref"></a>

#### ref *: [SourceRef](#glossa.domain.contracts.core.SourceRef)*

<a id="glossa.domain.contracts.extraction.ExtractedTarget.kind"></a>

#### kind *: [TargetKind](#glossa.domain.contracts.core.TargetKind)*

<a id="glossa.domain.contracts.extraction.ExtractedTarget.visibility"></a>

#### visibility *: [Visibility](#glossa.domain.contracts.core.Visibility)*

<a id="glossa.domain.contracts.extraction.ExtractedTarget.is_test_target"></a>

#### is_test_target *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.domain.contracts.extraction.ExtractedTarget.docstring"></a>

#### docstring *: [ExtractedDocstring](#glossa.domain.contracts.extraction.ExtractedDocstring) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.extraction.ExtractedTarget.signature"></a>

#### signature *: [SignatureFacts](#glossa.domain.contracts.extraction.SignatureFacts) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.extraction.ExtractedTarget.exceptions"></a>

#### exceptions *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[ExceptionFact](#glossa.domain.contracts.extraction.ExceptionFact), ...]*

<a id="glossa.domain.contracts.extraction.ExtractedTarget.warnings"></a>

#### warnings *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[WarningFact](#glossa.domain.contracts.extraction.WarningFact), ...]*

<a id="glossa.domain.contracts.extraction.ExtractedTarget.attributes"></a>

#### attributes *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[AttributeFact](#glossa.domain.contracts.extraction.AttributeFact), ...]*

<a id="glossa.domain.contracts.extraction.ExtractedTarget.module_symbols"></a>

#### module_symbols *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[ModuleSymbolFact](#glossa.domain.contracts.extraction.ModuleSymbolFact), ...]*

<a id="glossa.domain.contracts.extraction.ExtractedTarget.decorators"></a>

#### decorators *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.contracts.extraction.ExtractedTarget.related"></a>

#### related *: [RelatedTargets](#glossa.domain.contracts.extraction.RelatedTargets)*

<a id="glossa.domain.contracts.extraction.ExtractedTarget.suppression_lines"></a>

#### suppression_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]* *= ()*

<a id="module-glossa.domain.contracts.evaluation"></a>

<a id="evaluation"></a>

## Evaluation

Types for rule evaluation, diagnostics, and fix planning.

<a id="glossa.domain.contracts.evaluation.RuleOptionDescriptor"></a>

### *class* glossa.domain.contracts.evaluation.RuleOptionDescriptor(key, default, validator)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Declares one option that a rule accepts.

<a id="glossa.domain.contracts.evaluation.RuleOptionDescriptor.key"></a>

#### key *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.evaluation.RuleOptionDescriptor.default"></a>

#### default *: [object](https://docs.python.org/3/library/functions.html#object)*

<a id="glossa.domain.contracts.evaluation.RuleOptionDescriptor.validator"></a>

#### validator *: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable)[[[object](https://docs.python.org/3/library/functions.html#object), [str](https://docs.python.org/3/library/stdtypes.html#str)], [object](https://docs.python.org/3/library/functions.html#object)]*

<a id="glossa.domain.contracts.evaluation.RelatedTargetSnapshot"></a>

### *class* glossa.domain.contracts.evaluation.RelatedTargetSnapshot(ref: 'SourceRef', kind: 'TargetKind', docstring: 'ParsedDocstring | None', raw_docstring: 'ExtractedDocstring | None', signature: 'SignatureFacts | None')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.evaluation.RelatedTargetSnapshot.ref"></a>

#### ref *: [SourceRef](#glossa.domain.contracts.core.SourceRef)*

<a id="glossa.domain.contracts.evaluation.RelatedTargetSnapshot.kind"></a>

#### kind *: [TargetKind](#glossa.domain.contracts.core.TargetKind)*

<a id="glossa.domain.contracts.evaluation.RelatedTargetSnapshot.docstring"></a>

#### docstring *: [ParsedDocstring](domain-models.md#glossa.domain.models.ParsedDocstring) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.evaluation.RelatedTargetSnapshot.raw_docstring"></a>

#### raw_docstring *: [ExtractedDocstring](#glossa.domain.contracts.extraction.ExtractedDocstring) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.evaluation.RelatedTargetSnapshot.signature"></a>

#### signature *: [SignatureFacts](#glossa.domain.contracts.extraction.SignatureFacts) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.evaluation.ResolvedRelatedTargets"></a>

### *class* glossa.domain.contracts.evaluation.ResolvedRelatedTargets(parent: 'RelatedTargetSnapshot | None' = None, constructor: 'RelatedTargetSnapshot | None' = None, property_getter: 'RelatedTargetSnapshot | None' = None)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.evaluation.ResolvedRelatedTargets.parent"></a>

#### parent *: [RelatedTargetSnapshot](#glossa.domain.contracts.evaluation.RelatedTargetSnapshot) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

<a id="glossa.domain.contracts.evaluation.ResolvedRelatedTargets.constructor"></a>

#### constructor *: [RelatedTargetSnapshot](#glossa.domain.contracts.evaluation.RelatedTargetSnapshot) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

<a id="glossa.domain.contracts.evaluation.ResolvedRelatedTargets.property_getter"></a>

#### property_getter *: [RelatedTargetSnapshot](#glossa.domain.contracts.evaluation.RelatedTargetSnapshot) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

<a id="glossa.domain.contracts.evaluation.LintTarget"></a>

### *class* glossa.domain.contracts.evaluation.LintTarget(extracted, docstring, related)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Enriched target for rule evaluation.

Wraps an `ExtractedTarget` with a parsed docstring and resolved
related-target snapshots.  Explicitly typed properties forward known
fields for static type safety.  `__getattr__` provides a safety net
so that new `ExtractedTarget` fields are automatically available
without requiring manual forwarding.

<a id="glossa.domain.contracts.evaluation.LintTarget.extracted"></a>

#### extracted *: [ExtractedTarget](#glossa.domain.contracts.extraction.ExtractedTarget)*

<a id="glossa.domain.contracts.evaluation.LintTarget.docstring"></a>

#### docstring *: [ParsedDocstring](domain-models.md#glossa.domain.models.ParsedDocstring) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.evaluation.LintTarget.related"></a>

#### related *: [ResolvedRelatedTargets](#glossa.domain.contracts.evaluation.ResolvedRelatedTargets)*

<a id="glossa.domain.contracts.evaluation.LintTarget.ref"></a>

#### *property* ref *: [SourceRef](#glossa.domain.contracts.core.SourceRef)*

<a id="glossa.domain.contracts.evaluation.LintTarget.kind"></a>

#### *property* kind *: [TargetKind](#glossa.domain.contracts.core.TargetKind)*

<a id="glossa.domain.contracts.evaluation.LintTarget.visibility"></a>

#### *property* visibility *: [Visibility](#glossa.domain.contracts.core.Visibility)*

<a id="glossa.domain.contracts.evaluation.LintTarget.is_test_target"></a>

#### *property* is_test_target *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.domain.contracts.evaluation.LintTarget.raw_docstring"></a>

#### *property* raw_docstring *: [ExtractedDocstring](#glossa.domain.contracts.extraction.ExtractedDocstring) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.evaluation.LintTarget.signature"></a>

#### *property* signature *: [SignatureFacts](#glossa.domain.contracts.extraction.SignatureFacts) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.evaluation.LintTarget.exceptions"></a>

#### *property* exceptions *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[ExceptionFact](#glossa.domain.contracts.extraction.ExceptionFact), ...]*

<a id="glossa.domain.contracts.evaluation.LintTarget.warnings"></a>

#### *property* warnings *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[WarningFact](#glossa.domain.contracts.extraction.WarningFact), ...]*

<a id="glossa.domain.contracts.evaluation.LintTarget.attributes"></a>

#### *property* attributes *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[AttributeFact](#glossa.domain.contracts.extraction.AttributeFact), ...]*

<a id="glossa.domain.contracts.evaluation.LintTarget.module_symbols"></a>

#### *property* module_symbols *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[ModuleSymbolFact](#glossa.domain.contracts.extraction.ModuleSymbolFact), ...]*

<a id="glossa.domain.contracts.evaluation.LintTarget.decorators"></a>

#### *property* decorators *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.contracts.evaluation.RulePolicy"></a>

### *class* glossa.domain.contracts.evaluation.RulePolicy(enabled: 'bool', severity: 'Severity', options: 'Mapping[str, object]' = mappingproxy({}))

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.evaluation.RulePolicy.enabled"></a>

#### enabled *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.domain.contracts.evaluation.RulePolicy.severity"></a>

#### severity *: [Severity](#glossa.domain.contracts.core.Severity)*

<a id="glossa.domain.contracts.evaluation.RulePolicy.options"></a>

#### options *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/library/stdtypes.html#str), [object](https://docs.python.org/3/library/functions.html#object)]* *= mappingproxy({})*

<a id="glossa.domain.contracts.evaluation.EditKind"></a>

### *class* glossa.domain.contracts.evaluation.EditKind(value, names=<not given>, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

<a id="glossa.domain.contracts.evaluation.EditKind.INSERT"></a>

#### INSERT *= 'insert'*

<a id="glossa.domain.contracts.evaluation.EditKind.REPLACE"></a>

#### REPLACE *= 'replace'*

<a id="glossa.domain.contracts.evaluation.EditKind.DELETE"></a>

#### DELETE *= 'delete'*

<a id="glossa.domain.contracts.evaluation.DocstringEdit"></a>

### *class* glossa.domain.contracts.evaluation.DocstringEdit(kind: 'EditKind', span: 'DocstringSpan | None', text: 'str')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.evaluation.DocstringEdit.kind"></a>

#### kind *: [EditKind](#glossa.domain.contracts.evaluation.EditKind)*

<a id="glossa.domain.contracts.evaluation.DocstringEdit.span"></a>

#### span *: [DocstringSpan](domain-models.md#glossa.domain.models.DocstringSpan) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.evaluation.DocstringEdit.text"></a>

#### text *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.evaluation.FixPlan"></a>

### *class* glossa.domain.contracts.evaluation.FixPlan(description: 'str', target: 'SourceRef', edits: 'tuple[DocstringEdit, ...]', affected_rules: 'tuple[str, ...]')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.evaluation.FixPlan.description"></a>

#### description *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.evaluation.FixPlan.target"></a>

#### target *: [SourceRef](#glossa.domain.contracts.core.SourceRef)*

<a id="glossa.domain.contracts.evaluation.FixPlan.edits"></a>

#### edits *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[DocstringEdit](#glossa.domain.contracts.evaluation.DocstringEdit), ...]*

<a id="glossa.domain.contracts.evaluation.FixPlan.affected_rules"></a>

#### affected_rules *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.contracts.evaluation.Diagnostic"></a>

### *class* glossa.domain.contracts.evaluation.Diagnostic(rule: 'str', message: 'str', severity: 'Severity', target: 'SourceRef', span: 'TextSpan | None', fix: 'FixPlan | None' = None)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.contracts.evaluation.Diagnostic.rule"></a>

#### rule *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.evaluation.Diagnostic.message"></a>

#### message *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.contracts.evaluation.Diagnostic.severity"></a>

#### severity *: [Severity](#glossa.domain.contracts.core.Severity)*

<a id="glossa.domain.contracts.evaluation.Diagnostic.target"></a>

#### target *: [SourceRef](#glossa.domain.contracts.core.SourceRef)*

<a id="glossa.domain.contracts.evaluation.Diagnostic.span"></a>

#### span *: [TextSpan](#glossa.domain.contracts.core.TextSpan) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.contracts.evaluation.Diagnostic.fix"></a>

#### fix *: [FixPlan](#glossa.domain.contracts.evaluation.FixPlan) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*
