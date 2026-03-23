"""Linting orchestration: discover -> extract -> parse -> assemble targets -> run rules."""

from __future__ import annotations

from glossa.application.contracts import (
    Diagnostic,
    ExtractedTarget,
    GlossaConfig,
    LintTarget,
    RelatedTargetSnapshot,
)
from glossa.application.policy import (
    ResolvedRulePolicy,
    is_rule_suppressed,
    parse_inline_suppression,
    resolve_rule_policy,
)
from glossa.application.protocols import ExtractionPort
from glossa.application.registry import RuleRegistry
from glossa.domain.parsing import parse_docstring
from glossa.domain.rules import RuleContext


def lint_file(
    source_id: str,
    source_text: str,
    extraction_port: ExtractionPort,
    config: GlossaConfig,
    registry: RuleRegistry,
) -> tuple[Diagnostic, ...]:
    """Lint a single Python source file and return all diagnostics.

    Steps
    -----
    1. Extract lintable targets from *source_text* via *extraction_port*.
    2. For each extracted target, parse its docstring (if present) and
       assemble a :class:`~glossa.application.contracts.LintTarget`.
    3. Build a map of related target snapshots (constructor, parent, etc.)
       for each target.
    4. Filter rules by ``metadata.applies_to`` against the target kind.
    5. Resolve the per-rule policy via :func:`resolve_rule_policy`.  Skip
       rules that are disabled.
    6. Check inline suppressions and skip suppressed rules.
    7. Evaluate enabled rules and accumulate diagnostics.

    Parameters
    ----------
    source_id : str
        Project-relative POSIX path that uniquely identifies the source file.
    source_text : str
        Full text content of the source file.
    extraction_port : ExtractionPort
        Port used to extract lintable targets from the source text.
    config : GlossaConfig
        Active glossa configuration.
    registry : RuleRegistry
        Registry of built-in and plugin rules to evaluate.

    Returns
    -------
    tuple[Diagnostic, ...]
        All diagnostics produced for the file.
    """
    extracted_targets = extraction_port.extract(source_id, source_text)

    # Build a lookup from symbol_path key -> (extracted, parsed_docstring) so
    # we can assemble related-target snapshots without a second pass.
    from glossa.domain.models import ParsedDocstring

    parsed_map: dict[tuple[str, ...], tuple[ExtractedTarget, ParsedDocstring | None]] = {}
    for extracted in extracted_targets:
        parsed: ParsedDocstring | None = None
        if extracted.docstring is not None:
            parsed = parse_docstring(
                body=extracted.docstring.body,
                quote=extracted.docstring.quote,
                string_prefix=extracted.docstring.string_prefix,
                indentation=extracted.docstring.indentation,
            )
        parsed_map[extracted.ref.symbol_path] = (extracted, parsed)

    all_diagnostics: list[Diagnostic] = []

    for extracted in extracted_targets:
        _, parsed_docstring = parsed_map[extracted.ref.symbol_path]

        # Build the related-target snapshot map for this target.
        related_map: dict[str, RelatedTargetSnapshot] = _build_related_map(
            extracted, parsed_map
        )

        lint_target = assemble_lint_target(extracted, parsed_docstring, related_map)

        all_rules = registry.all_rules()
        applicable_rules = [
            rule
            for rule in all_rules
            if lint_target.kind in rule.metadata.applies_to
        ]

        # Parse inline suppression from the definition line, if available.
        inline_suppressions: tuple[str, ...] = ()
        if config.suppressions.inline_enabled and extracted.docstring is not None:
            # Attempt to find a suppression directive in the raw docstring body
            # (first line) or treat the body as a potential suppression target.
            for line in extracted.docstring.body.splitlines():
                parsed_sup = parse_inline_suppression(
                    line, config.suppressions.directive_prefix
                )
                if parsed_sup is not None:
                    inline_suppressions = parsed_sup
                    break

        for rule in applicable_rules:
            policy: ResolvedRulePolicy = resolve_rule_policy(
                rule_code=rule.metadata.code,
                source_id=source_id,
                config=config,
                default_severity=rule.metadata.default_severity,
            )

            if not policy.enabled:
                continue

            if config.suppressions.inline_enabled and is_rule_suppressed(
                rule.metadata.code, inline_suppressions
            ):
                continue

            context = RuleContext(policy=policy)
            diagnostics = rule.evaluate(lint_target, context)
            all_diagnostics.extend(diagnostics)

    return tuple(all_diagnostics)


def assemble_lint_target(
    extracted: ExtractedTarget,
    parsed: object | None,
    related_map: dict[str, RelatedTargetSnapshot],
) -> LintTarget:
    """Map an :class:`ExtractedTarget` and its parsed docstring into a :class:`LintTarget`.

    Parameters
    ----------
    extracted : ExtractedTarget
        The raw extracted target from the infrastructure layer.
    parsed : ParsedDocstring | None
        The parsed docstring for this target, or ``None`` if no docstring
        exists or parsing was skipped.
    related_map : dict[str, RelatedTargetSnapshot]
        Snapshots of related targets (e.g. ``"constructor"``, ``"parent"``).

    Returns
    -------
    LintTarget
        The assembled lint target ready for rule evaluation.
    """
    return LintTarget(
        ref=extracted.ref,
        kind=extracted.kind,
        visibility=extracted.visibility,
        is_test_target=extracted.is_test_target,
        docstring=parsed,  # type: ignore[arg-type]
        raw_docstring=extracted.docstring,
        signature=extracted.signature,
        exceptions=extracted.exceptions,
        warnings=extracted.warnings,
        attributes=extracted.attributes,
        module_symbols=extracted.module_symbols,
        decorators=extracted.decorators,
        related=related_map,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_related_map(
    extracted: ExtractedTarget,
    parsed_map: dict,
) -> dict[str, RelatedTargetSnapshot]:
    """Build a mapping of relationship name -> RelatedTargetSnapshot.

    Resolves ``constructor``, ``parent``, and ``property_getter`` references
    from the extracted target's :attr:`~ExtractedTarget.related` field using
    the pre-built *parsed_map*.

    Parameters
    ----------
    extracted : ExtractedTarget
        The target whose related references should be resolved.
    parsed_map : dict
        Mapping from symbol_path tuple to ``(ExtractedTarget, ParsedDocstring | None)``
        for all targets in the same file.

    Returns
    -------
    dict[str, RelatedTargetSnapshot]
        Mapping of relationship name to snapshot.  Only keys for which a
        matching target was found are included.
    """
    related_map: dict[str, RelatedTargetSnapshot] = {}

    ref_pairs = (
        ("constructor", extracted.related.constructor),
        ("parent", extracted.related.parent),
        ("property_getter", extracted.related.property_getter),
    )

    for key, ref in ref_pairs:
        if ref is None:
            continue
        entry = parsed_map.get(ref.symbol_path)
        if entry is None:
            continue
        related_extracted, related_parsed = entry
        related_map[key] = RelatedTargetSnapshot(
            ref=related_extracted.ref,
            kind=related_extracted.kind,
            docstring=related_parsed,
            raw_docstring=related_extracted.docstring,
            signature=related_extracted.signature,
        )

    return related_map
