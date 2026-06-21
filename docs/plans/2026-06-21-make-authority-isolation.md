# Bounded Make Authority Isolation

## Status: Completed

## Context

The repository protected its derived root, but GNU Make still accepted simple
caller-controlled root, shell, execution-mode, and tool-expression state for the
ordinary checked-in Makefile path. That state could redirect or suppress offline
transcription verification.

Startup makefiles can execute while GNU Make is parsing, before the repository Makefile can reject them. Extra `-f` files, target-specific variables, recipe replacement, and PATH-shadowed `python3` are caller-supplied Make or process programs outside the local Make trust boundary.

## Objectives

- Preserve the ordinary checked-in Makefile verification gate used by hosted CI.
- Reject unsupported non-executing and error-ignoring modes.
- Exercise all public targets from an external directory with hostile root and
  shell inputs, quoted paths, and literal-dollar tools for the sole checked-in
  Makefile path.
- Document that caller-supplied `MAKEFILES`, extra `-f` files, target-specific
  variables, recipe replacement, and PATH-shadowed `python3` are not sandboxed
  by this Makefile.
- Pin hosted verification dispatch to `/usr/bin/make`.

## Implementation

- Hardened the ordinary `Makefile` path against simple root, shell,
  unsupported-mode, and Make-syntax Python drift without changing audio,
  ffprobe, Whisper, dependency, or workflow-toolchain behavior.
- Added `scripts/test-makefile-root.sh` as an executable checked-in Makefile
  authority harness included in `make check`.
- Added `scripts/test-makefile-boundary.sh` as a post-landing boundary harness
  that reproduces caller-supplied Makefile, target-specific variable, replaced
  recipe, and PATH-shadowed Python cases as outside the local Make trust
  boundary and requires truthful documentation.
- Extended documentation, workflow contracts, and docs-plan checks to fail
  closed on overclaim regressions.

## Verification

- Root and external-directory `make check` passed formatting, Ruff, compilation,
  86 tests with four documented ML skips, mutation contracts, dependency checks,
  and direct-runtime audit.
- The ordinary authority harness passed checked-in Makefile target/root/shell
  combinations plus literal tool, raw Make-syntax rejection, and unsupported
  mode-flag cases.
- The boundary harness reproduces later target-specific `ROOT`/`PYTHON`, later
  target-specific and override `SHELL`/`.SHELLFLAGS`, replacement of all eight
  public recipes, and PATH-shadowed `python3` as documented outside-boundary
  cases rather than claiming they can be prevented locally by GNU Make.
- Hosted Python 3.10 and 3.12 remain the exact-head authority through
  `/usr/bin/make check`.

## Scope Boundary

This change does not alter upload handling, media probing, transcription,
cleanup, locking, model behavior, dependency pins, or deployment configuration.
It also does not claim to sandbox arbitrary caller-supplied Make programs.
