# Observed Verification Failure Propagation

## Status: Completed

## Context

`scripts/test-makefile-root.sh` exercised all eight public targets from a hostile
external directory and asserted, through a dispatch log written by a stand-in
`PYTHON`, that each target *invoked* the expected tool from the checked-in root.
That stand-in always exited `0`, so all 40 authority cases observed **dispatch**
and none observed **gating**: nothing in `make check` ever made a verification
command fail and asserted that `make check` then reported failure.

A dispatch log cannot see a discarded exit status, because the command still runs
and still logs. Appending `|| true` to the `test:` recipe left every existing pin
byte-identical, kept the dispatch log intact, and matched every substring recipe
contract in `scripts/check_docs_plans.py` (a substring pin is a prefix pin). With
that one token added, `make check` printed `2 failed` from pytest and exited `0`.

The same hole existed for `; true` and for GNU Make's leading `-` ignore-errors
prefix, on every command in `format`, `lint`, `test`, `build`, `audit`, and
`root-test`.

Recipe *replacement* of a public target was already caught: `check: verify audit`
and `verify: root-test format lint test build` carry no recipe of their own, and
prerequisites accumulate across duplicate rules, so a duplicate `test:` rule that
overrides the recipe stops dispatching pytest and the existing dispatch log fails
closed. Only the exit-status channel was unobserved.

## Objectives

- Make a failing verification command fail `make check`, and prove it by running
  each command to failure rather than asserting its source text exists.
- Keep the failure observer effective even when it runs inside the recipe whose
  exit status is discarded.
- Reject workflow-level verdict discarding.

## Implementation

- Extended `scripts/test-makefile-root.sh` with 34 failure-injection propagation
  cases. A stand-in `PYTHON` exits non-zero only for the single invocation whose
  argument list matches `TRANSCRIBE_FAIL_MATCH`, so each command is failed in
  isolation; each case asserts both that the command was actually dispatched (the
  injection is never a no-op on an untaken path) and that `make <target>`
  reported failure. Stub root-test scripts fail on demand through
  `TRANSCRIBE_FAIL_SCRIPT` to cover the two `root-test` recipe lines.
- Upgraded the Makefile recipe contracts in `scripts/check_docs_plans.py` from
  substring pins to tab-anchored whole-line pins required exactly once, so an
  appended `|| true` no longer prefix-matches. These run under `lint`, outside
  the `root-test` blast radius.
- Added an independent out-of-band CI step that runs the authority harness
  directly, so no Makefile recipe can discard its verdict, and made
  `continue-on-error` anywhere in the workflow a failure.
- Added `tests/test_repository.py` cross-guards, dispatched by the separate
  `test` target, that reject exit-status-discarding recipe lines and require the
  failure-injection cases to remain present.

The three guards are mutually cross-checking: `root-test` injection catches a
neutered `lint` or `test` line, the `lint` whole-line pins catch a neutered
`root-test` line, and the out-of-band CI step catches all of them.

## Verification

- `make check` passed on a clean tree: formatting, Ruff, compilation, 88 tests
  with four documented ML skips, mutation contracts, dependency checks, and
  direct-runtime audit.
- Failure injection, both directions, verified by hand against a real
  test-detected defect in `uploaded_audio_suffix`:
  - Before: `|| true` on the `test:` recipe plus the defect produced pytest
    `2 failed` and `make check` exit `0`.
  - After: the same mutation fails `make check` (exit `2`) with
    `make test reported success while the command matching 'pytest.main' failed`.
  - `|| true` on an inner `lint` command, `; true` on the `pip_audit` command,
    and a leading `-` on the `ruff check` command are each rejected.
  - `|| true` on the `root-test` line itself is rejected by the `lint` whole-line
    pin from outside the neutered recipe.
  - `continue-on-error: true` on the CI verification step, and removal of the
    out-of-band observer step, are each rejected.

## Scope Boundary

This change does not alter upload handling, media probing, transcription,
cleanup, locking, model behavior, dependency pins, or deployment configuration.
It does not widen the local Make trust boundary: caller-supplied `MAKEFILES`,
extra `-f` files, target-specific variables, shell overrides, and replaced
public-target recipes remain outside it, as `scripts/test-makefile-boundary.sh`
documents. An observer cannot observe its own removal; the out-of-band CI step
narrows that limit to a workflow edit.
