# Make Root Override Protection

## Status: Completed

## Context

The Makefile derives an absolute repository root so verification works outside
the checkout. Because the declaration is an ordinary GNU Make assignment, an
environment or command-line `ROOT` value can replace it and redirect Ruff,
source compilation, repository contracts, tests, and dependency-audit paths to
another tree while the command appears successful.

Python selection is intentionally configurable. Repository ownership is not:
every source and evidence path must remain anchored to the checkout containing
the invoked Makefile.

## Requirements

- Protect the derived repository root from environment and command-line
  reassignment.
- Preserve explicit `PYTHON` overrides and all seven public Make aliases.
- Prove repository and external working-directory invocations remain anchored
  under hostile root assignments.
- Add mutation-sensitive contracts for the declaration, assignment count and
  order, aliases, repository-owned paths, README index, and completed plan.
- Preserve transcription, upload, ffprobe, Whisper, dependency, workflow, and
  security behavior.

## Approach

Apply GNU Make's `override` directive only to the existing immediate root
assignment. Keep it before `PYTHON ?=` and extend the canonical documentation
checker with exact structural contracts. Exercise GNU Make precedence through
bounded dry-run cases and reject focused source mutations before the full
pinned package gate.

## Implementation Units

### Protect repository path ownership

- Update `Makefile` so exactly one protected root declaration owns every
  repository path.
- Keep the existing alias graph and configurable Python interpreter.

### Add adversarial contracts

- Extend `scripts/check_docs_plans.py` with declaration count, ordering, alias,
  source/checker/test/dependency path, README, and plan requirements.
- Run all seven aliases from repository and external directories under hostile
  environment and command-line root assignments.
- Reject declaration, duplication, ordering, alias, path, documentation, and
  plan-state mutations.

### Record completed evidence

- Index this plan from `README.md`.
- Mark it completed only after focused, mutation, full package, review,
  artifact, secret, and exact-diff validation succeeds.

## Risks And Mitigations

- Protecting the interpreter would break supported test-environment selection.
  Only `ROOT` becomes an override; `PYTHON ?=` remains unchanged and tested.
- Checking one declaration string could miss a later reassignment or bypass.
  Count all root assignments and require the complete alias graph and
  repository-owned command paths.
- Repository-local validation could hide working-directory assumptions. Run
  every alias from an external directory as well.

## Scope Boundaries

This change does not modify application logic, accepted media formats, upload
limits, duration checks, subprocess isolation, temporary-file lifecycle,
transcription locking, Streamlit UI, package pins, or workflow policy.

## Work Completed

- Protected the derived repository root with GNU Make's `override` directive
  while preserving explicit Python interpreter selection and all aliases.
- Added declaration-count, ordering, alias, repository-path, README, and plan
  contracts to the canonical checker.
- Indexed the completed evidence without modifying application, test,
  dependency, workflow, or security behavior.

## Verification Results

- All seven public aliases passed dry-run verification from repository and
  external working directories under hostile environment and command-line
  `ROOT` assignments, for 28 bounded cases; explicit `PYTHON` overrides remained
  effective.
- Eight declaration protection, duplicate assignment, ordering, alias,
  checker-path, README, missing-plan, and incomplete-plan mutations were
  rejected.
- A disposable exact-source snapshot passed the pinned Python 3.12.8
  `make check` gate under an explicit timeout: Ruff format and lint, 71 tests,
  source compilation, repository contracts, `pip check`, and `pip-audit` with no
  known runtime vulnerabilities.
- The completed plan record passed the same full gate from the repository and
  an external working directory.
- Plan-aware correctness, build-integrity, security, testing, maintainability,
  reliability, and project-standards review found no actionable findings.
- Exact diff, protected application/test/workflow/dependency path,
  generated-artifact, changed-line secret, and whitespace audits passed.
