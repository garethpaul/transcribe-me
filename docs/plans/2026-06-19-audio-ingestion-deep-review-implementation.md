# Audio Ingestion Deep Review Implementation Plan

Status: Completed. Verified with `make check`.

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Land a consolidated, evidence-backed security boundary for uploaded audio before Whisper model work.

**Architecture:** Extend the existing validation pipeline with a fixed-shape ffprobe metadata contract and bounded request admission. Keep all temporary-file and lock ownership in `transcribe_with_lock` so cleanup is exactly once.

**Tech Stack:** Python 3.10+, Streamlit, openai-whisper, ffprobe/ffmpeg, pytest, Ruff, GitHub Actions.

---

### Task 1: Probe metadata contract

**Files:**
- Modify: `tests/test_app.py`
- Modify: `app.py`

**Step 1:** Add failing tests for first-audio-stream selection, fixed metadata fields, oversized output, missing audio, container/codec mismatch, channel limits, and sample-rate limits.

**Step 2:** Run the focused tests and verify failures identify missing metadata validation.

**Step 3:** Replace duration-only parsing with a bounded metadata parser and conservative allowlists/limits.

**Step 4:** Run the focused tests and verify they pass.

### Task 2: File and admission ownership

**Files:**
- Modify: `tests/test_app.py`
- Modify: `app.py`

**Step 1:** Add failing tests for regular-file/no-symlink probing, mode `0600`, and rejection beyond one active plus one queued request.

**Step 2:** Run the tests and verify the new ownership expectations fail.

**Step 3:** Add the regular-file check and bounded admission semaphore while preserving nested cleanup and lock release.

**Step 4:** Run concurrency and cleanup tests and verify they pass.

### Task 3: Repository contracts and documentation

**Files:**
- Modify: `README.md`
- Modify: `SECURITY.md`
- Modify: `CHANGES.md`
- Modify: `scripts/check_docs_plans.py`
- Modify: `tests/test_repository.py`

**Step 1:** Add failing repository-policy assertions for the new constants, tests, workflow permissions, and root-safe Make behavior.

**Step 2:** Update documentation and policy checks to match runtime behavior.

**Step 3:** Run root and external-directory verification.

### Task 4: Security and dependency evidence

**Files:**
- Modify only if an audit identifies a concrete issue.

**Step 1:** Run isolated dependency checks and vulnerability audits.

**Step 2:** Scan current tree and full Git history without printing candidate values.

**Step 3:** Run hostile mutations against the metadata and admission invariants.

### Task 5: Consolidate and land

**Files:**
- Update the top stacked PR branch.

**Step 1:** Push the reviewed head and wait for exact-head hosted checks.

**Step 2:** Merge the stack safely into protected `main`.

**Step 3:** Close fully superseded PRs, verify exact-main checks, and report final SHA and residual risk.
