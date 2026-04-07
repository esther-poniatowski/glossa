# Processing Pipeline

End-to-end flow for both lint and fix modes. Each step feeds into the next; the
pipeline is orchestrated by the application layer.

```text
1. Bootstrap      Build the application services and explicit rule registry in adapters/bootstrap.py.
2. Load config    Read config files, merge CLI overrides, resolve rule policy.
3. Discover       Enumerate Python sources through DiscoveryPort.
4. Extract        Parse each file with ast and emit ExtractedTarget DTOs.
5. Parse          Convert raw docstrings into ParsedDocstring values.
6. Assemble       Build LintTarget snapshots with related entities.
7. Select rules   Filter by target kind, policy, suppressions, and severity overrides.
8. Evaluate       Run rules independently and collect diagnostics / fix plans.
9. Resolve fixes  Detect conflicts, reject unsafe fix groups, and build source edits.
10. Validate      Reparse source, re-extract changed targets, rerun affected rules.
11. Report        Emit diagnostics, operational errors, and fix results.
```
