---
phase: 24-robuustheid
plan: 01
subsystem: cli, storage, engine
tags: [resource-leak, empty-id-guard, parse-logging, team-size-validation]

requires:
  - phase: 23-rapportage-inkorten
    provides: compact report formatter
provides:
  - WebPusher always closed via try/finally
  - Empty decision_id rejected early
  - LLM parse failure warnings logged
  - Team size mismatch warnings logged
affects: []

tech-stack:
  added: []
  patterns: [try-finally-resource-cleanup, early-return-guard, parse-failure-logging]

key-files:
  created: []
  modified: [deliberators/__main__.py, deliberators/storage.py, deliberators/engine.py, tests/test_storage.py, tests/test_engine.py]

key-decisions:
  - "Parse failures log warnings but don't raise — fallback behavior preserved"
  - "Team size validation uses expected_analysts/expected_editors params, not global state"

duration: ~10min
started: 2026-03-22
completed: 2026-03-22
---

# Phase 24 Plan 01: Robuustheid Summary

**4 robustness fixes: WebPusher leak, empty decision_id, parse failure logging, team size validation**

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: WebPusher closed on error | Pass | try/finally wraps engine.run() block |
| AC-2: Empty decision_id rejected | Pass | Early return None for empty/whitespace |
| AC-3: Team size validation | Pass | Warnings logged for expected vs actual count |
| AC-4: Parse failure logging | Pass | All 3 parsers log warnings on unparseable output |
| AC-5: All tests pass | Pass | 1172 passed, 0 failed, 54 skipped |

## Files Modified

| File | Change |
|------|--------|
| `deliberators/__main__.py` | try/finally around engine.run() block |
| `deliberators/storage.py` | Empty/whitespace guard in load() |
| `deliberators/engine.py` | Parse failure + size mismatch warnings in all 3 parsers |
| `tests/test_storage.py` | +2 tests (empty, whitespace) |
| `tests/test_engine.py` | +4 tests (3x parse garbage warning, 1x size mismatch) |

## Deviations from Plan

None.

---
*Phase: 24-robuustheid, Plan: 01*
*Completed: 2026-03-22*
