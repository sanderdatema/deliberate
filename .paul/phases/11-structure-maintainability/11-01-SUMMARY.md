---
phase: 11-structure-maintainability
plan: 01
subsystem: engine
tags: [refactoring, dead-code, module-extraction, autodiscovery, config]

requires:
  - phase: 10-reliability-fixes
    provides: error handling, validation, WebPusher client reuse
provides:
  - Configurable summarizer via Preset.summarizer field
  - WebPusher as standalone module (deliberators/web_pusher.py)
  - Persona autodiscovery (no hardcoded STANDARD_PERSONAS)
  - Dead code removed from formatter.py
affects: [12-defensive-hardening]

tech-stack:
  added: []
  patterns: [config-driven summarizer identification, file-based autodiscovery]

key-files:
  created:
    - deliberators/web_pusher.py
  modified:
    - deliberators/formatter.py
    - deliberators/__main__.py
    - deliberators/models.py
    - deliberators/engine.py
    - deliberators/loader.py
    - config.yaml
    - tests/test_cli.py
    - tests/test_engine.py
    - tests/test_loader.py

key-decisions:
  - "Summarizer identified via Preset.summarizer field, not hardcoded string or last-editor convention"
  - "discover_custom() removed entirely — load_all() handles all personas via glob"
  - "Line 46 style variable in formatter.py is NOT dead code (used on line 47) — only line 35 removed"

patterns-established:
  - "Config-driven role identification: use dataclass fields to identify special roles, not magic strings"
  - "Autodiscovery pattern: glob *.yaml, exclude schema.yaml, key by stem"

duration: ~10min
completed: 2026-03-19
---

# Phase 11 Plan 01: Structure & Maintainability Summary

**4 MEDIUM-priority structural fixes: configurable summarizer, dead code removal, WebPusher extraction, persona autodiscovery — zero behavioral changes.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~10 min |
| Completed | 2026-03-19 |
| Tasks | 3 completed |
| Files modified | 10 (1 created, 9 modified) |
| Tests added | 7 new (3 summarizer + 4 autodiscovery) |
| Total tests | 521 passed, 25 skipped |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Magic string removed from engine | Pass | `engine.py` uses `preset.summarizer` — no hardcoded "samenvatter" |
| AC-2: Dead code removed from formatter | Pass | Unused `style` variable on line 35 deleted; line 46 kept (IS used) |
| AC-3: WebPusher in own module | Pass | `deliberators/web_pusher.py` created, `__main__.py` imports from it |
| AC-4: Persona autodiscovery | Pass | `STANDARD_PERSONAS` and `discover_custom()` removed, `load_all()` globs |
| AC-5: All tests pass | Pass | 521 passed (+3 from 518), 0 regressions |

## Accomplishments

- Engine no longer contains hardcoded "samenvatter" string — summarizer role is configurable per preset via `Preset.summarizer` field in `config.yaml`
- WebPusher extracted to standalone module `deliberators/web_pusher.py`, reducing `__main__.py` from god-module to focused CLI entry point
- `STANDARD_PERSONAS` frozenset eliminated — adding a new persona now requires only adding a `.yaml` file to the personas directory
- Dead `style` variable removed from formatter analyst section (line 35 was computed but never used)

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `deliberators/web_pusher.py` | Created | WebPusher class extracted from __main__.py |
| `deliberators/formatter.py` | Modified | Removed dead `style` variable (line 35) |
| `deliberators/__main__.py` | Modified | Import WebPusher from new module, removed inline class + discover_custom usage |
| `deliberators/models.py` | Modified | Added `summarizer: str \| None = None` to Preset |
| `deliberators/engine.py` | Modified | `if editor_name == preset.summarizer:` replaces magic string |
| `deliberators/loader.py` | Modified | Removed STANDARD_PERSONAS, rewrote load_all as autodiscovery, removed discover_custom |
| `config.yaml` | Modified | Added `summarizer: samenvatter` to general presets |
| `tests/test_cli.py` | Modified | Updated WebPusher import path |
| `tests/test_engine.py` | Modified | +3 tests: summarizer routing, no-summarizer, code preset |
| `tests/test_loader.py` | Modified | Replaced STANDARD_PERSONAS refs with EXPECTED_PERSONA_NAMES, 4 new autodiscovery tests |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Preset.summarizer field (not last-editor convention) | Explicit config > implicit convention; code presets have no summarizer | Config.yaml is the single source of truth for preset behavior |
| Remove discover_custom entirely | load_all now globs all *.yaml — custom personas are just personas | Simpler API, fewer methods, zero friction for adding personas |
| Keep formatter line 46 style var | It IS used on line 47 for editor headers — plan's initial analysis was corrected during execution | Only true dead code removed |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Corrected analysis | 1 | Plan self-corrected within Task 1 description |

**Total impact:** None — plan already contained the correction (line 46 `style` is used, only line 35 removed).

The plan noted `test_formatter.py` in `files_modified` but this file doesn't exist — formatter tests live in `test_cli.py`. No impact.

## Issues Encountered

None.

## Next Phase Readiness

**Ready:**
- All MEDIUM-priority findings resolved
- Codebase is cleaner: no magic strings, no dead code, no god-module, no hardcoded persona lists
- Phase 12 (Defensive Hardening) can proceed with LOW-priority items

**Concerns:**
- None

**Blockers:**
- None — Phase 12 (path sanitization, tuple in frozen dataclass, CodeContextBuilder refactor) can proceed

---
*Phase: 11-structure-maintainability, Plan: 01*
*Completed: 2026-03-19*
