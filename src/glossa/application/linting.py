"""Linting orchestration and analyzed-file assembly."""

from __future__ import annotations

from dataclasses import dataclass

from glossa.application.configuration import GlossaConfig
from glossa.application.policy import (
    is_rule_suppressed,
    parse_inline_suppression,
    resolve_rule_policy,
)
from glossa.application.protocols import ExtractionPort
from glossa.application.registry import RuleRegistry
from glossa.application.contracts import (
    Diagnostic,
    ExtractedTarget,
    LintTarget,
    RelatedTargetSnapshot,
    ResolvedRelatedTargets,
)
from glossa.domain.models import ParsedDocstring
from glossa.domain.parsing import parse_docstring
from glossa.domain.rules import RuleContext


@dataclass(frozen=True)
class AnalyzedTarget:
    lint_target: LintTarget
    diagnostics: tuple[Diagnostic, ...]


@dataclass(frozen=True)
class AnalyzedFile:
    source_id: str
    source_text: str
    targets: tuple[AnalyzedTarget, ...]

    @property
    def diagnostics(self) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []
        for target in self.targets:
            diagnostics.extend(target.diagnostics)
        return tuple(diagnostics)


def analyze_file(
    source_id: str,
    source_text: str,
    extraction_port: ExtractionPort,
    config: GlossaConfig,
    registry: RuleRegistry,
) -> AnalyzedFile:
    """Analyze a single Python source file and return structured results."""
    extracted_targets = extraction_port.extract(source_id, source_text)

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

    all_rules = registry.all_rules()
    analyzed_targets: list[AnalyzedTarget] = []

    for extracted in extracted_targets:
        _, parsed_docstring = parsed_map[extracted.ref.symbol_path]
        related = _build_related_targets(extracted, parsed_map)
        lint_target = assemble_lint_target(extracted, parsed_docstring, related)
        inline_suppressions = _resolve_inline_suppressions(
            extracted,
            directive_prefix=config.suppressions.directive_prefix,
        )

        diagnostics: list[Diagnostic] = []
        for rule in all_rules:
            meta = rule.metadata
            if lint_target.kind not in meta.applies_to:
                continue
            if meta.requires_docstring and lint_target.docstring is None:
                continue
            if meta.requires_signature and lint_target.signature is None:
                continue

            policy = resolve_rule_policy(
                rule_metadata=rule.metadata,
                source_id=source_id,
                config=config,
            )
            if not policy.enabled:
                continue
            if config.suppressions.inline_enabled and is_rule_suppressed(
                rule.metadata.code, inline_suppressions
            ):
                continue

            diagnostics.extend(rule.evaluate(
                lint_target,
                RuleContext(policy=policy, section_order=config.rules.section_order),
            ))

        analyzed_targets.append(
            AnalyzedTarget(
                lint_target=lint_target,
                diagnostics=tuple(diagnostics),
            )
        )

    return AnalyzedFile(
        source_id=source_id,
        source_text=source_text,
        targets=tuple(analyzed_targets),
    )


def assemble_lint_target(
    extracted: ExtractedTarget,
    parsed: ParsedDocstring | None,
    related: ResolvedRelatedTargets,
) -> LintTarget:
    """Map an extracted target into the pure lint target used by rules."""
    return LintTarget(
        extracted=extracted,
        docstring=parsed,
        related=related,
    )


def find_analyzed_target(
    analyzed_file: AnalyzedFile,
    symbol_path: tuple[str, ...],
) -> AnalyzedTarget | None:
    """Return the analyzed target for *symbol_path*, if present."""
    for target in analyzed_file.targets:
        if target.lint_target.ref.symbol_path == symbol_path:
            return target
    return None


def _resolve_inline_suppressions(
    extracted: ExtractedTarget,
    directive_prefix: str,
) -> tuple[str, ...]:
    suppressions: list[str] = []
    for line in extracted.suppression_lines:
        parsed = parse_inline_suppression(line, directive_prefix)
        if parsed is not None:
            suppressions.extend(parsed)
    return tuple(suppressions)


def _resolve_snapshot(
    ref,
    parsed_map: dict[tuple[str, ...], tuple[ExtractedTarget, ParsedDocstring | None]],
) -> RelatedTargetSnapshot | None:
    if ref is None:
        return None
    entry = parsed_map.get(ref.symbol_path)
    if entry is None:
        return None
    related_extracted, related_parsed = entry
    return RelatedTargetSnapshot(
        ref=related_extracted.ref,
        kind=related_extracted.kind,
        docstring=related_parsed,
        raw_docstring=related_extracted.docstring,
        signature=related_extracted.signature,
    )


def _build_related_targets(
    extracted: ExtractedTarget,
    parsed_map: dict[tuple[str, ...], tuple[ExtractedTarget, ParsedDocstring | None]],
) -> ResolvedRelatedTargets:
    return ResolvedRelatedTargets(
        constructor=_resolve_snapshot(extracted.related.constructor, parsed_map),
        parent=_resolve_snapshot(extracted.related.parent, parsed_map),
        property_getter=_resolve_snapshot(extracted.related.property_getter, parsed_map),
    )
