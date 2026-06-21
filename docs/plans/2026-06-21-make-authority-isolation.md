# Make Authority Isolation

## Status: Completed

## Context

The repository protected its derived root, but GNU Make still accepted caller-
controlled shell, startup-file, execution-mode, and tool-expression state. That
state could redirect or suppress offline transcription verification.

## Objectives

- Freeze the shell and preserve literal trusted Python executable overrides.
- Reject unsupported startup files, extra makefiles, non-executing modes, and
  error-ignoring modes.
- Require every public target to pass the same repository authority boundary.
- Exercise all public targets from an external directory with hostile root and
  shell inputs, quoted paths, literal-dollar tools, and startup attempts.
- Pin hosted verification dispatch to `/usr/bin/make`.

## Implementation

- Hardened `Makefile` startup and target authority without changing audio,
  ffprobe, Whisper, dependency, or workflow-toolchain behavior.
- Added `scripts/test-makefile-root.sh` as an executable adversarial authority
  harness included in `make check`.
- Extended documentation and workflow contracts to fail closed on regression.

## Verification

- Root and external-directory `make check` passed formatting, Ruff, compilation,
  86 tests with four documented ML skips, mutation contracts, dependency checks,
  and direct-runtime audit.
- The authority harness passed all target/root/shell combinations plus literal
  tool, raw Make-syntax, startup-file, extra-makefile, and mode-flag cases.
- Hosted Python 3.10 and 3.12 remain the exact-head authority.

## Scope Boundary

This change does not alter upload handling, media probing, transcription,
cleanup, locking, model behavior, dependency pins, or deployment configuration.
