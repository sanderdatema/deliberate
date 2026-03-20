---
phase: 13-package-data-bundling
plan: 01
subsystem: packaging
tags: [pyproject, package-data, hatchling, entry-point]

requires:
  - phase: 12-defensive-hardening
    provides: clean codebase, all v0.4 findings resolved
provides:
  - Bundled personas and config.yaml inside deliberators/data/
  - get_data_path() helper for locating bundled data
  - `deliberators` CLI entry point via [project.scripts]
  - Version 0.5.0
affects: [14-fallback-loader, 15-slash-command-update]

tech-stack:
  added: [hatchling]
  patterns: [package_data bundling via subpackage, Path(__file__).parent for data location]

key-files:
  created:
    - deliberators/data/__init__.py
    - deliberators/data/config.yaml
    - deliberators/data/personas/*.yaml
    - tests/test_package.py
  modified:
    - pyproject.toml
    - deliberators/__init__.py

key-decisions:
  - "hatchling as build backend — required by uv for [project.scripts] to work"
  - "Bundled data as subpackage (deliberators/data/) with __init__.py — simplest approach for hatchling auto-inclusion"
  - "Root-level personas/ and config.yaml kept — backward compatible for development"

patterns-established:
  - "get_data_path() returns Path to bundled data — use for fallback in Phase 14"
  - "deliberators/data/ mirrors root-level structure — personas/ subdir + config.yaml"

duration: ~10min
completed: 2026-03-20
---

# Phase 13 Plan 01: Package Data Bundling Summary

**Bundled personas + config inside package, added hatchling build system, CLI entry point, and get_data_path() helper — package is now self-contained.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~10 min |
| Completed | 2026-03-20 |
| Tasks | 3 completed |
| Files created | 28 (1 __init__.py + 1 config + 26 personas + 1 test) |
| Files modified | 2 (pyproject.toml, __init__.py) |
| Tests added | 5 new |
| Total tests | 534 passed, 25 skipped |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Bundled data exists | Pass | 26 YAML files in deliberators/data/personas/ + config.yaml |
| AC-2: Scripts entry point | Pass | `uv run deliberators --help` works |
| AC-3: get_data_path() helper | Pass | Returns valid Path, config.yaml and personas/ found |
| AC-4: Version 0.5.0 | Pass | pyproject.toml version = "0.5.0" |
| AC-5: All tests pass | Pass | 534 passed (+5 new), 0 regressions |

## Accomplishments

- Package is self-contained: `deliberators/data/` has all personas and config
- CLI available as `deliberators` command (not just `python -m deliberators`)
- `get_data_path()` provides stable API for Phase 14 fallback logic
- hatchling build backend enables proper wheel building for `uv tool install`

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `deliberators/data/__init__.py` | Created | Makes data dir a package for auto-inclusion |
| `deliberators/data/config.yaml` | Created | Bundled copy of root config |
| `deliberators/data/personas/*.yaml` | Created | Bundled copies of all 26 persona files |
| `pyproject.toml` | Modified | [build-system], [project.scripts], version 0.5.0, hatch config |
| `deliberators/__init__.py` | Modified | Added get_data_path() helper |
| `tests/test_package.py` | Created | 5 tests for bundled data verification |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| hatchling as build backend | uv requires [build-system] for [project.scripts] to install entry points | Standard Python packaging, no vendor lock-in |
| Data as subpackage with __init__.py | Simplest way to ensure hatchling includes it in wheel | No explicit include patterns needed |
| Keep root-level files | Backward compatible for `uv run python -m deliberators` during development | Phase 14 will add fallback: CWD → bundled |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Essential |

**Total impact:** Essential fix — without [build-system], scripts entry points don't install.

### Auto-fixed Issues

**1. Missing [build-system] section**
- **Found during:** Task 2 (pyproject.toml update)
- **Issue:** `uv sync` warned "Skipping installation of entry points because project is not packaged"
- **Fix:** Added `[build-system] requires = ["hatchling"]` and `build-backend = "hatchling.build"`
- **Verification:** `uv run deliberators --help` works after fix

## Issues Encountered

None beyond the auto-fixed deviation.

## Next Phase Readiness

**Ready:**
- `get_data_path()` available for Phase 14 fallback loader
- Package builds and installs correctly
- All 534 tests pass

**Concerns:**
- None

**Blockers:**
- None — Phase 14 (Fallback Loader) can proceed

---
*Phase: 13-package-data-bundling, Plan: 01*
*Completed: 2026-03-20*
