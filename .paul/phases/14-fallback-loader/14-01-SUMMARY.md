---
phase: 14-fallback-loader
plan: 01
subsystem: loader
tags: [fallback, path-resolution, global-install, config]

requires:
  - phase: 13-package-data-bundling
    provides: bundled data in deliberators/data/, get_data_path()
provides:
  - resolve_config_path() with 3-level fallback chain
  - resolve_personas_dir() with 3-level fallback chain
  - CLI works from any directory
affects: [15-slash-command-update]

tech-stack:
  added: []
  patterns: [CWD → user config → bundled fallback chain]

key-files:
  created: []
  modified:
    - deliberators/loader.py
    - deliberators/__main__.py
    - tests/test_loader.py

key-decisions:
  - "Use _BUNDLED_DATA_DIR = Path(__file__).parent / 'data' instead of importing get_data_path() to avoid circular import"
  - "Default argparse values kept as Path('config.yaml') and Path('personas') — resolve functions detect these sentinels"
  - "Fallback chain: CWD → ~/.config/deliberators/ → bundled package data"

patterns-established:
  - "Fallback resolution: check existence at each level, return first match"
  - "Sentinel detection: if explicit path equals default, apply fallback; otherwise use as-is"

duration: ~8min
completed: 2026-03-20
---

# Phase 14 Plan 01: Fallback Loader Summary

**3-level fallback chain (CWD → ~/.config/deliberators/ → bundled) for config and personas — CLI now works from any directory.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~8 min |
| Completed | 2026-03-20 |
| Tasks | 3 completed |
| Files modified | 3 |
| Tests added | 6 new |
| Total tests | 540 passed, 25 skipped |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Bundled fallback for config | Pass | Falls back to deliberators/data/config.yaml when CWD and user dir empty |
| AC-2: Bundled fallback for personas | Pass | Falls back to deliberators/data/personas/ |
| AC-3: CWD takes priority | Pass | CWD config.yaml/personas/ found first |
| AC-4: User config over bundled | Pass | ~/.config/deliberators/ checked before bundled |
| AC-5: CLI works from any dir | Pass | `uv run deliberators --help` works everywhere |
| AC-6: All tests pass | Pass | 540 passed (+6 new), 0 regressions |

## Accomplishments

- `resolve_config_path()` and `resolve_personas_dir()` implement 3-level fallback
- CLI is now globally usable — no longer requires CWD to be the project directory
- User can override with `~/.config/deliberators/` or explicit `--config`/`--personas-dir` flags

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `deliberators/loader.py` | Modified | Added resolve_config_path(), resolve_personas_dir(), _BUNDLED_DATA_DIR, _USER_CONFIG_DIR |
| `deliberators/__main__.py` | Modified | Uses resolve functions before loading config/personas |
| `tests/test_loader.py` | Modified | +6 fallback chain tests with monkeypatch |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| _BUNDLED_DATA_DIR instead of get_data_path() import | Circular import: loader → __init__ → engine → loader | Same result, no circular dependency |
| Sentinel detection for defaults | Keeps argparse clean — no need for None defaults or custom actions | resolve() knows when to apply fallback vs use explicit path |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 2 | Essential |

### Auto-fixed Issues

**1. Circular import**
- **Found during:** Task 1
- **Issue:** `from deliberators import get_data_path` in loader.py caused circular import (loader → __init__ → engine → loader)
- **Fix:** Used `_BUNDLED_DATA_DIR = Path(__file__).parent / "data"` instead

**2. Test directory creation order**
- **Found during:** Task 3
- **Issue:** `monkeypatch.chdir(empty_cwd)` called before `empty_cwd.mkdir()`
- **Fix:** Moved mkdir before chdir

## Issues Encountered

None beyond auto-fixed deviations.

## Next Phase Readiness

**Ready:**
- Fallback chain working end-to-end
- Phase 15 (Slash Command Update) can update commands to use `deliberators` CLI

**Concerns:**
- None

**Blockers:**
- None

---
*Phase: 14-fallback-loader, Plan: 01*
*Completed: 2026-03-20*
