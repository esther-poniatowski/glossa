<a id="domain-rules"></a>

# Domain Rules

Rule system for docstring linting. Each rule family inspects an extracted docstring and emits diagnostics with optional fix plans.

<a id="module-glossa.domain.rules"></a>

<a id="rule-base"></a>

## Rule base

Rule system for docstring linting.

<a id="glossa.domain.rules.RuleMetadata"></a>

### *class* glossa.domain.rules.RuleMetadata(name: 'str', group: 'str', description: 'str', default_severity: 'Severity', applies_to: 'frozenset[TargetKind]', fixable: 'bool', requires_docstring: 'bool' = True, requires_signature: 'bool' = False, option_schema: 'tuple[RuleOptionDescriptor, ...]' = <factory>)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.rules.RuleMetadata.name"></a>

#### name *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.rules.RuleMetadata.group"></a>

#### group *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.rules.RuleMetadata.description"></a>

#### description *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.rules.RuleMetadata.default_severity"></a>

#### default_severity *: [Severity](domain-contracts.md#glossa.domain.contracts.core.Severity)*

<a id="glossa.domain.rules.RuleMetadata.applies_to"></a>

#### applies_to *: [frozenset](https://docs.python.org/3/library/stdtypes.html#frozenset)[[TargetKind](domain-contracts.md#glossa.domain.contracts.core.TargetKind)]*

<a id="glossa.domain.rules.RuleMetadata.fixable"></a>

#### fixable *: [bool](https://docs.python.org/3/library/functions.html#bool)*

<a id="glossa.domain.rules.RuleMetadata.requires_docstring"></a>

#### requires_docstring *: [bool](https://docs.python.org/3/library/functions.html#bool)* *= True*

<a id="glossa.domain.rules.RuleMetadata.requires_signature"></a>

#### requires_signature *: [bool](https://docs.python.org/3/library/functions.html#bool)* *= False*

<a id="glossa.domain.rules.RuleMetadata.option_schema"></a>

#### option_schema *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[RuleOptionDescriptor](domain-contracts.md#glossa.domain.contracts.evaluation.RuleOptionDescriptor), ...]*

<a id="glossa.domain.rules.RuleContext"></a>

### *class* glossa.domain.rules.RuleContext(policy: 'RulePolicy', section_order: 'tuple[str, ...]' = <factory>)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.rules.RuleContext.policy"></a>

#### policy *: [RulePolicy](domain-contracts.md#glossa.domain.contracts.evaluation.RulePolicy)*

<a id="glossa.domain.rules.RuleContext.section_order"></a>

#### section_order *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.rules.Rule"></a>

### *class* glossa.domain.rules.Rule(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

<a id="glossa.domain.rules.Rule.metadata"></a>

#### metadata *: [RuleMetadata](#glossa.domain.rules.RuleMetadata)*

<a id="glossa.domain.rules.Rule.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.make_diagnostic"></a>

### glossa.domain.rules.make_diagnostic(rule, target, context, message, span=None, fix=None)

Build a Diagnostic with invariants enforced.

Converts any `DocstringSpan` to a file-level `TextSpan` using the
target’s raw docstring body span.  `Diagnostic.span` is always
`TextSpan | None`.

<a id="module-glossa.domain.rules.presence"></a>

<a id="presence-rules"></a>

## Presence rules

Presence and Coverage rules for the glossa docstring linter.

<a id="glossa.domain.rules.presence.MissingModuleDocstring"></a>

### glossa.domain.rules.presence.MissingModuleDocstring

alias of `missing-module-docstring`

<a id="glossa.domain.rules.presence.MissingClassDocstring"></a>

### glossa.domain.rules.presence.MissingClassDocstring

alias of `missing-class-docstring`

<a id="glossa.domain.rules.presence.MissingCallableDocstring"></a>

### *class* glossa.domain.rules.presence.MissingCallableDocstring

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Missing public callable docstring.

<a id="glossa.domain.rules.presence.MissingCallableDocstring.metadata"></a>

#### metadata *= RuleMetadata(name='missing-callable-docstring', group='presence', description='Missing public callable docstring.', default_severity=<Severity.CONVENTION: 'convention'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.FUNCTION: 'function'>}), fixable=False, requires_docstring=False, requires_signature=False, option_schema=(RuleOptionDescriptor(key='include_test_functions', default=False, validator=<function validate_bool>), RuleOptionDescriptor(key='include_private_helpers', default=False, validator=<function validate_bool>)))*

<a id="glossa.domain.rules.presence.MissingCallableDocstring.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.presence.MissingParametersSection"></a>

### *class* glossa.domain.rules.presence.MissingParametersSection

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Missing Parameters section for documentable parameters.

<a id="glossa.domain.rules.presence.MissingParametersSection.metadata"></a>

#### metadata *= RuleMetadata(name='missing-parameters-section', group='presence', description='Missing Parameters section for documentable parameters.', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.CLASS: 'class'>, <TargetKind.METHOD: 'method'>, <TargetKind.FUNCTION: 'function'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=(RuleOptionDescriptor(key='include_test_functions', default=False, validator=<function validate_bool>), RuleOptionDescriptor(key='include_non_public_helpers', default=False, validator=<function validate_bool>)))*

<a id="glossa.domain.rules.presence.MissingParametersSection.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.presence.MissingReturnsSection"></a>

### glossa.domain.rules.presence.MissingReturnsSection

alias of `missing-returns-section`

<a id="glossa.domain.rules.presence.MissingYieldsSection"></a>

### glossa.domain.rules.presence.MissingYieldsSection

alias of `missing-yields-section`

<a id="glossa.domain.rules.presence.MissingRaisesSection"></a>

### glossa.domain.rules.presence.MissingRaisesSection

alias of `missing-raises-section`

<a id="glossa.domain.rules.presence.MissingWarnsSection"></a>

### glossa.domain.rules.presence.MissingWarnsSection

alias of `missing-warns-section`

<a id="glossa.domain.rules.presence.MissingModuleInventory"></a>

### *class* glossa.domain.rules.presence.MissingModuleInventory

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Missing module Classes/Functions inventory when required.

<a id="glossa.domain.rules.presence.MissingModuleInventory.metadata"></a>

#### metadata *= RuleMetadata(name='missing-module-inventory', group='presence', description='Missing module Classes/Functions inventory when required.', default_severity=<Severity.CONVENTION: 'convention'>, applies_to=frozenset({<TargetKind.MODULE: 'module'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=(RuleOptionDescriptor(key='inventory_threshold', default=3, validator=<function validate_positive_int>),))*

<a id="glossa.domain.rules.presence.MissingModuleInventory.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.presence.MissingAttributesSection"></a>

### *class* glossa.domain.rules.presence.MissingAttributesSection

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Missing Attributes section where class attributes require documentation.

<a id="glossa.domain.rules.presence.MissingAttributesSection.metadata"></a>

#### metadata *= RuleMetadata(name='missing-attributes-section', group='presence', description='Missing Attributes section where class attributes require documentation.', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.CLASS: 'class'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=(RuleOptionDescriptor(key='include_test_functions', default=False, validator=<function validate_bool>), RuleOptionDescriptor(key='include_non_public_helpers', default=False, validator=<function validate_bool>), RuleOptionDescriptor(key='dataclass_requires_attributes', default=False, validator=<function validate_bool>)))*

<a id="glossa.domain.rules.presence.MissingAttributesSection.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.presence.ParamsInInitNotClass"></a>

### *class* glossa.domain.rules.presence.ParamsInInitNotClass

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Constructor parameters documented in \_\_init_\_ instead of class docstring.

<a id="glossa.domain.rules.presence.ParamsInInitNotClass.metadata"></a>

#### metadata *= RuleMetadata(name='params-in-init-not-class', group='presence', description='Constructor parameters documented in \_\_init_\_ instead of class docstring.', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.CLASS: 'class'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.presence.ParamsInInitNotClass.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.presence.MissingDeprecationDirective"></a>

### *class* glossa.domain.rules.presence.MissingDeprecationDirective

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Missing deprecation directive for deprecated public API.

<a id="glossa.domain.rules.presence.MissingDeprecationDirective.metadata"></a>

#### metadata *= RuleMetadata(name='missing-deprecation-directive', group='presence', description='Missing deprecation directive for deprecated public API.', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.CLASS: 'class'>, <TargetKind.MODULE: 'module'>, <TargetKind.FUNCTION: 'function'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.presence.MissingDeprecationDirective.evaluate"></a>

#### evaluate(target, context)

<a id="module-glossa.domain.rules.prose"></a>

<a id="prose-rules"></a>

## Prose rules

Prose and Summary Format rules.

<a id="glossa.domain.rules.prose.NonImperativeSummary"></a>

### *class* glossa.domain.rules.prose.NonImperativeSummary

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Summary line is not imperative where imperative voice is required.

<a id="glossa.domain.rules.prose.NonImperativeSummary.metadata"></a>

#### metadata *= RuleMetadata(name='non-imperative-summary', group='prose', description='Summary line is not imperative where imperative voice is required.', default_severity=<Severity.CONVENTION: 'convention'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.FUNCTION: 'function'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=(RuleOptionDescriptor(key='include_test_functions', default=False, validator=<function validate_bool>), RuleOptionDescriptor(key='include_non_public_helpers', default=False, validator=<function validate_bool>), RuleOptionDescriptor(key='property_requires_imperative_summary', default=False, validator=<function validate_bool>)))*

<a id="glossa.domain.rules.prose.NonImperativeSummary.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.prose.MissingPeriod"></a>

### *class* glossa.domain.rules.prose.MissingPeriod

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Summary line missing terminal period.

<a id="glossa.domain.rules.prose.MissingPeriod.metadata"></a>

#### metadata *= RuleMetadata(name='missing-period', group='prose', description='Summary line missing terminal period.', default_severity=<Severity.CONVENTION: 'convention'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.CLASS: 'class'>, <TargetKind.MODULE: 'module'>, <TargetKind.FUNCTION: 'function'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.prose.MissingPeriod.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.prose.MissingBlankAfterSummary"></a>

### *class* glossa.domain.rules.prose.MissingBlankAfterSummary

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Missing blank line after summary when body follows.

<a id="glossa.domain.rules.prose.MissingBlankAfterSummary.metadata"></a>

#### metadata *= RuleMetadata(name='missing-blank-after-summary', group='prose', description='Missing blank line after summary when body follows.', default_severity=<Severity.CONVENTION: 'convention'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.CLASS: 'class'>, <TargetKind.MODULE: 'module'>, <TargetKind.FUNCTION: 'function'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.prose.MissingBlankAfterSummary.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.prose.FirstPersonVoice"></a>

### *class* glossa.domain.rules.prose.FirstPersonVoice

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

First-person voice in docstring.

<a id="glossa.domain.rules.prose.FirstPersonVoice.metadata"></a>

#### metadata *= RuleMetadata(name='first-person-voice', group='prose', description='First-person voice in docstring.', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.CLASS: 'class'>, <TargetKind.MODULE: 'module'>, <TargetKind.FUNCTION: 'function'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.prose.FirstPersonVoice.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.prose.SecondPersonVoice"></a>

### *class* glossa.domain.rules.prose.SecondPersonVoice

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Second-person voice in docstring.

<a id="glossa.domain.rules.prose.SecondPersonVoice.metadata"></a>

#### metadata *= RuleMetadata(name='second-person-voice', group='prose', description='Second-person voice in docstring.', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.CLASS: 'class'>, <TargetKind.MODULE: 'module'>, <TargetKind.FUNCTION: 'function'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.prose.SecondPersonVoice.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.prose.MarkdownInDocstring"></a>

### *class* glossa.domain.rules.prose.MarkdownInDocstring

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Markdown syntax where RST is required.

<a id="glossa.domain.rules.prose.MarkdownInDocstring.metadata"></a>

#### metadata *= RuleMetadata(name='markdown-in-docstring', group='prose', description='Markdown syntax where RST is required.', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.CLASS: 'class'>, <TargetKind.MODULE: 'module'>, <TargetKind.FUNCTION: 'function'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.prose.MarkdownInDocstring.evaluate"></a>

#### evaluate(target, context)

<a id="module-glossa.domain.rules.structure"></a>

<a id="structure-rules"></a>

## Structure rules

Section Structure and Placement rules for glossa.

<a id="glossa.domain.rules.structure.MalformedUnderline"></a>

### *class* glossa.domain.rules.structure.MalformedUnderline

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Section underline is malformed.

<a id="glossa.domain.rules.structure.MalformedUnderline.metadata"></a>

#### metadata *= RuleMetadata(name='malformed-underline', group='structure', description='Section underline is malformed', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.CLASS: 'class'>, <TargetKind.MODULE: 'module'>, <TargetKind.FUNCTION: 'function'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.structure.MalformedUnderline.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.structure.SectionOrder"></a>

### *class* glossa.domain.rules.structure.SectionOrder

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Section order violates NumPy policy.

<a id="glossa.domain.rules.structure.SectionOrder.metadata"></a>

#### metadata *= RuleMetadata(name='section-order', group='structure', description='Section order violates NumPy policy', default_severity=<Severity.CONVENTION: 'convention'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.CLASS: 'class'>, <TargetKind.MODULE: 'module'>, <TargetKind.FUNCTION: 'function'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.structure.SectionOrder.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.structure.UndocumentedParameter"></a>

### *class* glossa.domain.rules.structure.UndocumentedParameter

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Undocumented parameter present in signature.

<a id="glossa.domain.rules.structure.UndocumentedParameter.metadata"></a>

#### metadata *= RuleMetadata(name='undocumented-parameter', group='structure', description='Undocumented parameter present in signature', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.CLASS: 'class'>, <TargetKind.METHOD: 'method'>, <TargetKind.FUNCTION: 'function'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.structure.UndocumentedParameter.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.structure.ExtraneousParameter"></a>

### *class* glossa.domain.rules.structure.ExtraneousParameter

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Extraneous parameter appears in docstring.

<a id="glossa.domain.rules.structure.ExtraneousParameter.metadata"></a>

#### metadata *= RuleMetadata(name='extraneous-parameter', group='structure', description='Extraneous parameter appears in docstring', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.CLASS: 'class'>, <TargetKind.METHOD: 'method'>, <TargetKind.FUNCTION: 'function'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.structure.ExtraneousParameter.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.structure.MalformedDeprecation"></a>

### *class* glossa.domain.rules.structure.MalformedDeprecation

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Deprecation directive is malformed or misplaced.

<a id="glossa.domain.rules.structure.MalformedDeprecation.metadata"></a>

#### metadata *= RuleMetadata(name='malformed-deprecation', group='structure', description='Deprecation directive is malformed or misplaced', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.CLASS: 'class'>, <TargetKind.MODULE: 'module'>, <TargetKind.FUNCTION: 'function'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.structure.MalformedDeprecation.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.structure.RstDirectiveInsteadOfSection"></a>

### *class* glossa.domain.rules.structure.RstDirectiveInsteadOfSection

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

RST directive used where a NumPy section exists.

<a id="glossa.domain.rules.structure.RstDirectiveInsteadOfSection.metadata"></a>

#### metadata *= RuleMetadata(name='rst-directive-instead-of-section', group='structure', description='RST directive used where a NumPy section exists', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.CLASS: 'class'>, <TargetKind.MODULE: 'module'>, <TargetKind.FUNCTION: 'function'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.structure.RstDirectiveInsteadOfSection.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.structure.ExamplesInNonEntryModule"></a>

### *class* glossa.domain.rules.structure.ExamplesInNonEntryModule

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Examples appears in a non-entry-point module docstring.

<a id="glossa.domain.rules.structure.ExamplesInNonEntryModule.metadata"></a>

#### metadata *= RuleMetadata(name='examples-in-non-entry-module', group='structure', description='Examples appears in a non-entry-point module docstring', default_severity=<Severity.CONVENTION: 'convention'>, applies_to=frozenset({<TargetKind.MODULE: 'module'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=(RuleOptionDescriptor(key='api_entry_modules', default=(), validator=<function validate_string_tuple>),))*

<a id="glossa.domain.rules.structure.ExamplesInNonEntryModule.evaluate"></a>

#### evaluate(target, context)

<a id="module-glossa.domain.rules.typed_entries"></a>

<a id="typed-entry-rules"></a>

## Typed-entry rules

Typed Entry Consistency rules for the glossa docstring linter.

<a id="glossa.domain.rules.typed_entries.MissingParamType"></a>

### *class* glossa.domain.rules.typed_entries.MissingParamType

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Parameter type missing from docstring.

<a id="glossa.domain.rules.typed_entries.MissingParamType.metadata"></a>

#### metadata *= RuleMetadata(name='missing-param-type', group='typed-entries', description='Parameter type missing from docstring', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.CLASS: 'class'>, <TargetKind.METHOD: 'method'>, <TargetKind.FUNCTION: 'function'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.typed_entries.MissingParamType.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.typed_entries.ParamTypeMismatch"></a>

### *class* glossa.domain.rules.typed_entries.ParamTypeMismatch

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Parameter type mismatches annotation.

<a id="glossa.domain.rules.typed_entries.ParamTypeMismatch.metadata"></a>

#### metadata *= RuleMetadata(name='param-type-mismatch', group='typed-entries', description='Parameter type mismatches annotation', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.CLASS: 'class'>, <TargetKind.METHOD: 'method'>, <TargetKind.FUNCTION: 'function'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.typed_entries.ParamTypeMismatch.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.typed_entries.MissingReturnType"></a>

### *class* glossa.domain.rules.typed_entries.MissingReturnType

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Return type missing from docstring.

<a id="glossa.domain.rules.typed_entries.MissingReturnType.metadata"></a>

#### metadata *= RuleMetadata(name='missing-return-type', group='typed-entries', description='Return type missing from docstring', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.FUNCTION: 'function'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.typed_entries.MissingReturnType.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.typed_entries.ReturnTypeMismatch"></a>

### *class* glossa.domain.rules.typed_entries.ReturnTypeMismatch

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Return type mismatches annotation.

<a id="glossa.domain.rules.typed_entries.ReturnTypeMismatch.metadata"></a>

#### metadata *= RuleMetadata(name='return-type-mismatch', group='typed-entries', description='Return type mismatches annotation', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.FUNCTION: 'function'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.typed_entries.ReturnTypeMismatch.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.typed_entries.YieldTypeMismatch"></a>

### *class* glossa.domain.rules.typed_entries.YieldTypeMismatch

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Yield type missing or mismatched.

<a id="glossa.domain.rules.typed_entries.YieldTypeMismatch.metadata"></a>

#### metadata *= RuleMetadata(name='yield-type-mismatch', group='typed-entries', description='Yield type missing or mismatched', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.FUNCTION: 'function'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.typed_entries.YieldTypeMismatch.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.typed_entries.MissingAttributeType"></a>

### *class* glossa.domain.rules.typed_entries.MissingAttributeType

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Attribute type missing where Attributes entry exists.

<a id="glossa.domain.rules.typed_entries.MissingAttributeType.metadata"></a>

#### metadata *= RuleMetadata(name='missing-attribute-type', group='typed-entries', description='Attribute type missing where Attributes entry exists', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.CLASS: 'class'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.typed_entries.MissingAttributeType.evaluate"></a>

#### evaluate(target, context)

<a id="module-glossa.domain.rules.anti_patterns"></a>

<a id="anti-pattern-rules"></a>

## Anti-pattern rules

Anti-Patterns rules for the glossa docstring linter.

<a id="glossa.domain.rules.anti_patterns.EmptyDocstring"></a>

### *class* glossa.domain.rules.anti_patterns.EmptyDocstring

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Fires when a docstring exists but its body is empty or whitespace-only.

<a id="glossa.domain.rules.anti_patterns.EmptyDocstring.metadata"></a>

#### metadata *= RuleMetadata(name='empty-docstring', group='anti-patterns', description='Empty docstring body.', default_severity=<Severity.WARNING: 'warning'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.CLASS: 'class'>, <TargetKind.MODULE: 'module'>, <TargetKind.FUNCTION: 'function'>}), fixable=False, requires_docstring=False, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.anti_patterns.EmptyDocstring.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.anti_patterns.TrivialDunderDocstring"></a>

### *class* glossa.domain.rules.anti_patterns.TrivialDunderDocstring

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Fires when a dunder method docstring trivially restates the method name.

<a id="glossa.domain.rules.anti_patterns.TrivialDunderDocstring.metadata"></a>

#### metadata *= RuleMetadata(name='trivial-dunder-docstring', group='anti-patterns', description='Trivial dunder method docstring.', default_severity=<Severity.CONVENTION: 'convention'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=(RuleOptionDescriptor(key='trivial_dunder_allowlist', default=('_\_init_\_', '_\_new_\_', '_\_post_init_\_', '_\_init_subclass_\_', '_\_class_getitem_\_'), validator=<function validate_string_tuple>), RuleOptionDescriptor(key='include_non_public_helpers', default=False, validator=<function validate_bool>)))*

<a id="glossa.domain.rules.anti_patterns.TrivialDunderDocstring.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.anti_patterns.RedundantReturnsNone"></a>

### *class* glossa.domain.rules.anti_patterns.RedundantReturnsNone

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Fires when a void callable has a Returns section listing only None.

<a id="glossa.domain.rules.anti_patterns.RedundantReturnsNone.metadata"></a>

#### metadata *= RuleMetadata(name='redundant-returns-none', group='anti-patterns', description='Redundant Returns None section for a function that does not return a value.', default_severity=<Severity.CONVENTION: 'convention'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.FUNCTION: 'function'>}), fixable=True, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.anti_patterns.RedundantReturnsNone.evaluate"></a>

#### evaluate(target, context)

<a id="glossa.domain.rules.anti_patterns.RstNoteWarningDirective"></a>

### *class* glossa.domain.rules.anti_patterns.RstNoteWarningDirective

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Fires when prose contains a RST `.. note::` or `.. warning::` directive.

<a id="glossa.domain.rules.anti_patterns.RstNoteWarningDirective.metadata"></a>

#### metadata *= RuleMetadata(name='rst-note-warning-directive', group='anti-patterns', description='Prose uses a RST note/warning directive; use a NumPy-style section instead.', default_severity=<Severity.CONVENTION: 'convention'>, applies_to=frozenset({<TargetKind.METHOD: 'method'>, <TargetKind.PROPERTY: 'property'>, <TargetKind.CLASS: 'class'>, <TargetKind.MODULE: 'module'>, <TargetKind.FUNCTION: 'function'>}), fixable=False, requires_docstring=True, requires_signature=False, option_schema=())*

<a id="glossa.domain.rules.anti_patterns.RstNoteWarningDirective.evaluate"></a>

#### evaluate(target, context)
