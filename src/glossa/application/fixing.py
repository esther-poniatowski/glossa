"""Fixing orchestration: resolve fix conflicts -> apply edits -> validate output."""

from __future__ import annotations

from dataclasses import dataclass

from glossa.application.contracts import (
    Diagnostic,
    FixPlan,
    GlossaConfig,
    SourceRef,
)
from glossa.application.protocols import FilePort
from glossa.domain.fixes import apply_edits_to_body, detect_conflicts, validate_fix_result


@dataclass(frozen=True)
class FixResult:
    target: SourceRef
    applied: tuple[FixPlan, ...]
    rejected: tuple[FixPlan, ...]
    validation_passed: bool


def apply_fixes(
    diagnostics: tuple[Diagnostic, ...],
    file_port: FilePort,
    config: GlossaConfig,
) -> tuple[FixResult, ...]:
    """Apply fix plans derived from *diagnostics* and return per-target results.

    Steps
    -----
    1. Group diagnostics that carry a fix plan by their ``target`` (source_id).
    2. For each target, collect all fix plans.
    3. Use :func:`~glossa.domain.fixes.detect_conflicts` to separate accepted
       from rejected plans (first plan wins on overlap).
    4. For each accepted plan, apply its edits to the docstring body via
       :func:`~glossa.domain.fixes.apply_edits_to_body`.
    5. When ``config.fix.validate_after_apply`` is ``True``, call
       :func:`~glossa.domain.fixes.validate_fix_result` on the edited body.
    6. When validation passes and ``config.fix.apply`` is not ``"never"``,
       write the result back to the source file via *file_port*.
    7. Return a :class:`FixResult` for every target that had at least one
       fixable diagnostic.

    Parameters
    ----------
    diagnostics : tuple[Diagnostic, ...]
        All diagnostics for one or more source files.  Only diagnostics whose
        ``fix`` field is not ``None`` are processed.
    file_port : FilePort
        Port used to read and write source file content.
    config : GlossaConfig
        Active glossa configuration, consulted for ``fix.apply`` and
        ``fix.validate_after_apply`` settings.

    Returns
    -------
    tuple[FixResult, ...]
        One :class:`FixResult` per source file that contained at least one
        fixable diagnostic.
    """
    # Step 1: group fix plans by source_id.
    plans_by_source: dict[str, list[FixPlan]] = {}
    ref_by_source: dict[str, SourceRef] = {}

    for diagnostic in diagnostics:
        if diagnostic.fix is None:
            continue
        source_id = diagnostic.target.source_id
        if source_id not in plans_by_source:
            plans_by_source[source_id] = []
            ref_by_source[source_id] = diagnostic.target
        plans_by_source[source_id].append(diagnostic.fix)

    results: list[FixResult] = []

    for source_id, plans in plans_by_source.items():
        target_ref = ref_by_source[source_id]

        # Step 3: resolve conflicts.
        accepted, rejected = detect_conflicts(tuple(plans))

        if not accepted:
            results.append(
                FixResult(
                    target=target_ref,
                    applied=(),
                    rejected=rejected,
                    validation_passed=True,
                )
            )
            continue

        # Step 4: apply edits.
        original_body = file_port.read(source_id)
        edited_body = original_body

        all_affected_rules: list[str] = []
        for plan in accepted:
            edited_body = apply_edits_to_body(edited_body, plan.edits)
            all_affected_rules.extend(plan.affected_rules)

        # Step 5: optional validation.
        validation_passed = True
        if config.fix.validate_after_apply:
            validation_passed, _ = validate_fix_result(
                original_body=original_body,
                edited_body=edited_body,
                affected_rules=tuple(all_affected_rules),
            )

        # Step 6: write back when allowed.
        if validation_passed and config.fix.apply != "never":
            file_port.write(source_id, edited_body)

        results.append(
            FixResult(
                target=target_ref,
                applied=accepted,
                rejected=rejected,
                validation_passed=validation_passed,
            )
        )

    return tuple(results)
