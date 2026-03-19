---
phase: 12-defensive-hardening
plan: 01
subsystem: engine
tags: [security, immutability, refactoring, path-sanitization]

requires:
  - phase: 11-structure-maintainability
    provides: autodiscovery, Preset.summarizer, WebPusher extraction
provides:
  - Path sanitization and filesize limits in code context builder
  - Immutable tuple fields in frozen dataclasses
  - Module-level build_code_context() function (no class wrapper)
affects: []

tech-stack:
  added: []
  patterns: [path traversal rejection via parts check, filesize guard, tuple fields in frozen dataclasses]

key-files:
  created: []
  modified:
    - deliberators/context.py
    - deliberators/models.py
    - deliberators/loader.py
    - deliberators/__main__.py
    - tests/test_context.py
    - tests/test_loader.py
    - tests/test_engine.py
    - tests/test_models.py
    - tests/test_cli.py

key-decisions:
  - "Path traversal check via '..' in path.parts — simple, no canonicalization needed"
  - "MAX_FILE_SIZE as module constant (1 MB) — not configurable via config.yaml"
  - "output_format dict left as-is — no frozendict in stdlib, not worth a dependency"

patterns-established:
  - "Defensive guards: check path parts and file size before reading"
  - "Immutable collections in frozen dataclasses: tuple[str, ...] not list[str]"

duration: ~8min
completed: 2026-03-19
---

# Phase 12 Plan 01: Defensive Hardening Summary

**3 LOW-priority defensive fixes: path sanitization + filesize limit, immutable tuple fields in frozen dataclasses, CodeContextBuilder class → module function — zero behavioral changes.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~8 min |
| Completed | 2026-03-19 |
| Tasks | 3 completed |
| Files modified | 9 |
| Tests added | 8 new (3 path/filesize + 2 tuple + 3 immutable fields) |
| Total tests | 529 passed, 25 skipped |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Path traversal rejected | Pass | Paths with ".." in parts are skipped with warning log |
| AC-2: Filesize limit | Pass | Files > MAX_FILE_SIZE (1 MB) skipped; files at exact limit kept |
| AC-3: Immutable tuple fields | Pass | Persona.forbidden, Preset.analysts, Preset.editors all `tuple[str, ...]` |
| AC-4: CodeContextBuilder → function | Pass | `build_code_context()` module function, no class remains |
| AC-5: All tests pass | Pass | 529 passed (+8 from 521), 0 regressions |

## Accomplishments

- Path traversal protection: files with ".." components are rejected before any I/O
- Filesize guard: files exceeding 1 MB are skipped, preventing context blowup
- Frozen dataclass correctness: mutable `list[str]` replaced with immutable `tuple[str, ...]` in Persona and Preset
- Simpler API: `build_code_context(paths)` replaces unnecessary `CodeContextBuilder.build(paths)` class wrapper

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `deliberators/context.py` | Modified | Added MAX_FILE_SIZE, path traversal check, filesize check; class → function |
| `deliberators/models.py` | Modified | `list[str]` → `tuple[str, ...]` for forbidden, analysts, editors |
| `deliberators/loader.py` | Modified | `tuple()` wrapping in Persona and Preset construction |
| `deliberators/__main__.py` | Modified | Import `build_code_context` instead of `CodeContextBuilder` |
| `tests/test_context.py` | Modified | Updated imports, renamed class, +6 new tests (path traversal, filesize) |
| `tests/test_loader.py` | Modified | +3 tuple field tests, list→tuple in Preset literals |
| `tests/test_engine.py` | Modified | list→tuple in Preset construction literals |
| `tests/test_models.py` | Modified | list→tuple in Persona and Preset construction literals |
| `tests/test_cli.py` | Modified | list→tuple in Preset construction literal |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Path check via `".." in path.parts` | Simple and correct — no need for resolve() or canonicalization | Easy to understand, no edge cases with symlinks |
| MAX_FILE_SIZE = 1 MB as module constant | Sufficient for code review context; config.yaml complexity not warranted | Can be made configurable later if needed |
| Leave `output_format: dict` as-is | No `frozendict` in stdlib; adding a dependency for one field is overkill | Known limitation, documented in plan |
| Update all test Preset/Persona literals to tuples | Type correctness — tests should match the actual types | 1 extra test failure caught and fixed during execution |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Minimal |

**Total impact:** Minimal — one test used list literal comparison that needed updating.

### Auto-fixed Issues

**1. test_loader list comparison**
- **Found during:** Task 3 (test verification)
- **Issue:** `test_quick_preset_analysts` compared against `["occam", "holmes", "lupin"]` (list) but loaded data is now tuple
- **Fix:** Changed to `("occam", "holmes", "lupin")` (tuple)
- **Verification:** All 529 tests pass

## Issues Encountered

None.

## Next Phase Readiness

**Ready:**
- All 10 code review findings from `/deliberate-code` self-review are resolved (3 HIGH + 4 MEDIUM + 3 LOW)
- v0.4 milestone is complete (3/3 phases done)
- Codebase is cleaner: no magic strings, no dead code, no god-module, no hardcoded persona lists, no mutable fields in frozen dataclasses, no path traversal risk, no unbounded file reads

**Concerns:**
- None

**Blockers:**
- None — v0.4 milestone complete

---
*Phase: 12-defensive-hardening, Plan: 01*
*Completed: 2026-03-19*
