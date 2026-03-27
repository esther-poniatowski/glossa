"""Application services for project-wide lint and fix runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from glossa.application.configuration import (
    FixApplyMode,
    GlossaConfig,
    OutputFormat,
    config_with_overrides,
)
from glossa.application.fixing import (
    FixRejection,
    FixRejectionReason,
    FixResult,
    FixTransformation,
    apply_fixes,
)
from glossa.application.linting import AnalyzedFile, analyze_file
from glossa.application.protocols import DiscoveryPort, ExtractionPort, FilePort
from glossa.application.registry import RuleRegistry
from glossa.application.contracts import Diagnostic
from glossa.errors import GlossaError


@dataclass(frozen=True)
class OperationalIssue:
    source_id: str | None
    message: str


@dataclass(frozen=True)
class LintRunResult:
    files: tuple[AnalyzedFile, ...]
    operational_issues: tuple[OperationalIssue, ...]
    effective_config: GlossaConfig

    @property
    def diagnostics(self) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []
        for analyzed_file in self.files:
            diagnostics.extend(analyzed_file.diagnostics)
        return tuple(diagnostics)


@dataclass(frozen=True)
class FixRunResult:
    results: tuple[FixResult, ...]
    fixable_diagnostics: tuple[Diagnostic, ...]
    operational_issues: tuple[OperationalIssue, ...]
    fix_enabled: bool

    @property
    def applied_count(self) -> int:
        return sum(len(result.applied) for result in self.results)

    @property
    def rejected_count(self) -> int:
        return sum(len(result.rejected) for result in self.results)


@dataclass(frozen=True)
class CheckRunResult:
    fixable_count: int
    operational_issues: tuple[OperationalIssue, ...]


class GlossaService:
    """Facade exposing intent-level lint and fix workflows."""

    def __init__(
        self,
        *,
        config: GlossaConfig,
        discovery: DiscoveryPort,
        extractor: ExtractionPort,
        file_port: FilePort,
        registry: RuleRegistry,
    ) -> None:
        self._config = config
        self._discovery = discovery
        self._extractor = extractor
        self._file_port = file_port
        self._registry = registry

    @property
    def config(self) -> GlossaConfig:
        return self._config

    def lint_paths(
        self,
        paths: Sequence[str],
        *,
        select: Sequence[str] | None = None,
        ignore: Sequence[str] | None = None,
        output_format: OutputFormat | None = None,
        color: bool | None = None,
    ) -> LintRunResult:
        config = config_with_overrides(
            self._config,
            select=select,
            ignore=ignore,
            output_format=output_format,
            color=color,
        )
        return self._analyze_paths(paths, config)

    def fix_paths(
        self,
        paths: Sequence[str],
        *,
        dry_run: bool = False,
        select: Sequence[str] | None = None,
        ignore: Sequence[str] | None = None,
    ) -> FixRunResult:
        config = config_with_overrides(self._config, select=select, ignore=ignore)
        lint_result = self._analyze_paths(paths, config)
        fixable = tuple(
            diagnostic
            for analyzed_file in lint_result.files
            for diagnostic in analyzed_file.diagnostics
            if diagnostic.fix is not None
        )
        if not config.fix.enabled or dry_run or not fixable:
            return FixRunResult(
                results=(),
                fixable_diagnostics=fixable,
                operational_issues=lint_result.operational_issues,
                fix_enabled=config.fix.enabled,
            )
        transformations = apply_fixes(
            analyzed_files=lint_result.files,
            config=config,
        )
        fix_results = tuple(
            self._finalize_transformation(t, config, lint_result.files)
            for t in transformations
        )
        return FixRunResult(
            results=fix_results,
            fixable_diagnostics=fixable,
            operational_issues=lint_result.operational_issues,
            fix_enabled=True,
        )

    def check_paths(
        self,
        paths: Sequence[str],
        *,
        select: Sequence[str] | None = None,
        ignore: Sequence[str] | None = None,
    ) -> CheckRunResult:
        lint_result = self._analyze_paths(
            paths,
            config_with_overrides(self._config, select=select, ignore=ignore),
        )
        fixable_count = sum(
            1
            for analyzed_file in lint_result.files
            for diagnostic in analyzed_file.diagnostics
            if diagnostic.fix is not None
        )
        return CheckRunResult(
            fixable_count=fixable_count,
            operational_issues=lint_result.operational_issues,
        )

    def lint_source(
        self,
        source_text: str,
        *,
        source_id: str = "__input__.py",
        select: Sequence[str] | None = None,
        ignore: Sequence[str] | None = None,
    ) -> tuple[Diagnostic, ...]:
        config = config_with_overrides(self._config, select=select, ignore=ignore)
        return analyze_file(
            source_id=source_id,
            source_text=source_text,
            extraction_port=self._extractor,
            config=config,
            registry=self._registry,
        ).diagnostics

    def _finalize_transformation(
        self,
        transformation: FixTransformation,
        config: GlossaConfig,
        analyzed_files: tuple[AnalyzedFile, ...],
    ) -> FixResult:
        rejected = list(transformation.rejected)

        if not transformation.accepted:
            return FixResult(
                source_id=transformation.source_id,
                applied=(),
                rejected=tuple(rejected),
                validation_passed=True,
            )

        validation_passed = True
        if config.fix.validate_after_apply:
            original = next(
                (f for f in analyzed_files if f.source_id == transformation.source_id),
                None,
            )
            if original is not None:
                try:
                    reanalyzed = analyze_file(
                        source_id=original.source_id,
                        source_text=transformation.edited_source,
                        extraction_port=self._extractor,
                        config=config,
                        registry=self._registry,
                    )
                except GlossaError as exc:
                    validation_passed = False
                    message = f"Edited source no longer analyzes cleanly: {exc}"
                else:
                    remaining = {
                        (d.target.symbol_path, d.code)
                        for d in reanalyzed.diagnostics
                    }
                    for plan in transformation.accepted:
                        for rule_code in plan.affected_rules:
                            if (plan.target.symbol_path, rule_code) in remaining:
                                validation_passed = False
                                message = (
                                    f"Rule {rule_code} still fires for "
                                    f"{'.'.join(plan.target.symbol_path) or '<module>'}."
                                )
                                break
                        if not validation_passed:
                            break

        if not validation_passed:
            for plan in transformation.accepted:
                rejected.append(
                    FixRejection(
                        plan=plan,
                        reason=FixRejectionReason.VALIDATION_FAILED,
                        details=message,
                    )
                )
            return FixResult(
                source_id=transformation.source_id,
                applied=(),
                rejected=tuple(rejected),
                validation_passed=False,
            )

        if config.fix.apply is not FixApplyMode.NEVER:
            self._file_port.write(transformation.source_id, transformation.edited_source)

        return FixResult(
            source_id=transformation.source_id,
            applied=transformation.accepted,
            rejected=tuple(rejected),
            validation_passed=True,
        )

    def _analyze_paths(
        self,
        paths: Sequence[str],
        config: GlossaConfig,
    ) -> LintRunResult:
        try:
            discovered = tuple(self._discovery.discover(paths))
        except GlossaError as exc:
            return LintRunResult(
                files=(),
                operational_issues=(OperationalIssue(source_id=None, message=str(exc)),),
                effective_config=config,
            )

        analyzed_files: list[AnalyzedFile] = []
        issues: list[OperationalIssue] = []

        for source_id in discovered:
            try:
                source_text = self._file_port.read(source_id)
                analyzed_files.append(
                    analyze_file(
                        source_id=source_id,
                        source_text=source_text,
                        extraction_port=self._extractor,
                        config=config,
                        registry=self._registry,
                    )
                )
            except GlossaError as exc:
                issues.append(OperationalIssue(source_id=source_id, message=str(exc)))

        return LintRunResult(
            files=tuple(analyzed_files),
            operational_issues=tuple(issues),
            effective_config=config,
        )
