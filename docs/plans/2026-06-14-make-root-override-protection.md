# Make Root Override Protection

## Status: Planned

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

## Verification Plan

- Run the focused documentation checker and Make dry-run checks.
- Exercise all aliases from both working directories under hostile root
  assignments while preserving explicit Python selection.
- Reject eight focused structural and evidence mutations.
- Run the full pinned `make check` gate with an explicit timeout from both
  repository and external working directories.
- Review the exact plan-scoped diff and audit generated artifacts, changed-line
  secrets, whitespace, and protected application/workflow/dependency paths.
