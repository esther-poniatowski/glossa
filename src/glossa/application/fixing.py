"""Source-level fix orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from glossa.application.configuration import FixApplyMode, GlossaConfig
from glossa.application.linting import AnalyzedFile, analyze_file
from glossa.application.protocols import ExtractionPort, FilePort
from glossa.application.registry import RuleRegistry
from glossa.application.contracts import EditKind, FixPlan, SourceRef
from glossa.domain.fixes import intervals_overlap
from glossa.errors import GlossaError


class FixRejectionReason(Enum):
    CONFLICT = "conflict"
    UNSUPPORTED = "unsupported"
    VALIDATION_FAILED = "validation_failed"


@dataclass(frozen=True)
class FixRejection:
    plan: FixPlan
    reason: FixRejectionReason
    details: str


@dataclass(frozen=True)
class FixResult:
    source_id: str
    applied: tuple[FixPlan, ...]
    rejected: tuple[FixRejection, ...]
    validation_passed: bool


@dataclass(frozen=True)
class _SourceEdit:
    kind: EditKind
    start_offset: int
    end_offset: int
    text: str


@dataclass(frozen=True)
class _ResolvedFixPlan:
    plan: FixPlan
    target: SourceRef
    edits: tuple[_SourceEdit, ...]


def apply_fixes(
    analyzed_files: tuple[AnalyzedFile, ...],
    file_port: FilePort,
    config: GlossaConfig,
    extraction_port: ExtractionPort,
    registry: RuleRegistry,
) -> tuple[FixResult, ...]:
    """Apply validated source-level fixes for analyzed files."""
    results: list[FixResult] = []

    for analyzed_file in analyzed_files:
        fix_plans = [
            diagnostic.fix
            for target in analyzed_file.targets
            for diagnostic in target.diagnostics
            if diagnostic.fix is not None
        ]
        if not fix_plans:
            continue

        resolved: list[_ResolvedFixPlan] = []
        rejected: list[FixRejection] = []
        for plan in fix_plans:
            analyzed_target = _find_target(analyzed_file, plan.target)
            if analyzed_target is None or analyzed_target.extracted.docstring is None:
                rejected.append(
                    FixRejection(
                        plan=plan,
                        reason=FixRejectionReason.UNSUPPORTED,
                        details="Fix target is missing an extracted docstring body.",
                    )
                )
                continue
            try:
                resolved.append(
                    _resolve_fix_plan(
                        analyzed_file.source_text,
                        analyzed_target.extracted.docstring,
                        plan,
                    )
                )
            except ValueError as exc:
                rejected.append(
                    FixRejection(
                        plan=plan,
                        reason=FixRejectionReason.UNSUPPORTED,
                        details=str(exc),
                    )
                )

        accepted, conflict_rejections = _partition_conflicts(tuple(resolved))
        rejected.extend(conflict_rejections)

        if not accepted:
            results.append(
                FixResult(
                    source_id=analyzed_file.source_id,
                    applied=(),
                    rejected=tuple(rejected),
                    validation_passed=True,
                )
            )
            continue

        edited_source = _apply_source_edits(
            analyzed_file.source_text,
            tuple(
                source_edit
                for plan in accepted
                for source_edit in plan.edits
            ),
        )

        validation_passed, validation_message = _validate_edited_source(
            original=analyzed_file,
            edited_source=edited_source,
            config=config,
            extraction_port=extraction_port,
            registry=registry,
            accepted=accepted,
        )

        applied: tuple[FixPlan, ...] = ()
        if validation_passed:
            applied = tuple(plan.plan for plan in accepted)
            if config.fix.apply is not FixApplyMode.NEVER:
                file_port.write(analyzed_file.source_id, edited_source)
        else:
            for plan in accepted:
                rejected.append(
                    FixRejection(
                        plan=plan.plan,
                        reason=FixRejectionReason.VALIDATION_FAILED,
                        details=validation_message,
                    )
                )

        results.append(
            FixResult(
                source_id=analyzed_file.source_id,
                applied=applied,
                rejected=tuple(rejected),
                validation_passed=validation_passed,
            )
        )

    return tuple(results)


def _find_target(analyzed_file: AnalyzedFile, target_ref: SourceRef):
    for target in analyzed_file.targets:
        if target.extracted.ref == target_ref:
            return target
    return None


def _resolve_fix_plan(
    source_text: str,
    docstring,
    plan: FixPlan,
) -> _ResolvedFixPlan:
    line_offsets = _line_offsets(source_text)
    body_start = _offset_for_position(
        line_offsets,
        docstring.body_span.start.line,
        docstring.body_span.start.column,
    )

    source_edits: list[_SourceEdit] = []
    for edit in plan.edits:
        if edit.span is None:
            raise ValueError(
                "Edit is missing an explicit docstring span."
            )
        start = body_start + edit.span.start_offset
        end = body_start + edit.span.end_offset
        source_edits.append(
            _SourceEdit(
                kind=edit.kind,
                start_offset=start,
                end_offset=end,
                text=edit.text,
            )
        )

    return _ResolvedFixPlan(
        plan=plan,
        target=plan.target,
        edits=tuple(source_edits),
    )


def _partition_conflicts(
    plans: tuple[_ResolvedFixPlan, ...],
) -> tuple[tuple[_ResolvedFixPlan, ...], tuple[FixRejection, ...]]:
    accepted: list[_ResolvedFixPlan] = []
    rejected: list[FixRejection] = []

    for candidate in plans:
        if any(_plans_overlap(candidate, existing) for existing in accepted):
            rejected.append(
                FixRejection(
                    plan=candidate.plan,
                    reason=FixRejectionReason.CONFLICT,
                    details="Fix overlaps with an earlier accepted source edit.",
                )
            )
            continue
        accepted.append(candidate)

    return tuple(accepted), tuple(rejected)


def _plans_overlap(a: _ResolvedFixPlan, b: _ResolvedFixPlan) -> bool:
    return any(_edits_overlap(left, right) for left in a.edits for right in b.edits)


def _edits_overlap(a: _SourceEdit, b: _SourceEdit) -> bool:
    return intervals_overlap(a.start_offset, a.end_offset, b.start_offset, b.end_offset)


def _apply_source_edits(source_text: str, edits: tuple[_SourceEdit, ...]) -> str:
    ordered = sorted(edits, key=lambda edit: edit.start_offset, reverse=True)
    result = source_text
    for edit in ordered:
        if edit.kind is EditKind.REPLACE:
            result = result[: edit.start_offset] + edit.text + result[edit.end_offset :]
        elif edit.kind is EditKind.DELETE:
            result = result[: edit.start_offset] + result[edit.end_offset :]
        elif edit.kind is EditKind.INSERT:
            result = result[: edit.start_offset] + edit.text + result[edit.start_offset :]
    return result


def _validate_edited_source(
    *,
    original: AnalyzedFile,
    edited_source: str,
    config: GlossaConfig,
    extraction_port: ExtractionPort,
    registry: RuleRegistry,
    accepted: tuple[_ResolvedFixPlan, ...],
) -> tuple[bool, str]:
    if not config.fix.validate_after_apply:
        return True, ""

    try:
        reanalyzed = analyze_file(
            source_id=original.source_id,
            source_text=edited_source,
            extraction_port=extraction_port,
            config=config,
            registry=registry,
        )
    except GlossaError as exc:
        return False, f"Edited source no longer analyzes cleanly: {exc}"

    remaining = {
        (diagnostic.target.symbol_path, diagnostic.code)
        for diagnostic in reanalyzed.diagnostics
    }

    for plan in accepted:
        for rule_code in plan.plan.affected_rules:
            if (plan.target.symbol_path, rule_code) in remaining:
                return (
                    False,
                    f"Rule {rule_code} still fires for {'.'.join(plan.target.symbol_path) or '<module>'}.",
                )

    return True, ""


def _line_offsets(source_text: str) -> list[int]:
    offsets = [0]
    for idx, char in enumerate(source_text):
        if char == "\n":
            offsets.append(idx + 1)
    return offsets


def _offset_for_position(line_offsets: list[int], line: int, column: int) -> int:
    return line_offsets[line - 1] + column
