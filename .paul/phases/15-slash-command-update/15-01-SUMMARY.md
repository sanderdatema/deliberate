---
phase: 15-slash-command-update
plan: 01
subsystem: commands
tags: [slash-commands, path-resolution, global-install]

requires:
  - phase: 14-fallback-loader
    provides: resolve_config_path(), resolve_personas_dir()
provides:
  - Global slash commands with dynamic path resolution
  - /deliberate and /deliberate-code work from any project directory
affects: []

tech-stack:
  added: []
  patterns: [dynamic path resolution via uv run python -c in slash commands]

key-files:
  created: []
  modified:
    - .claude/commands/deliberate.md
    - .claude/commands/deliberate-code.md

key-decisions:
  - "Path resolution via Bash uv run python -c command — simplest approach, no new dependencies"
  - "Fallback to CWD paths if deliberators not installed — backward compatible"

patterns-established:
  - "Step 0.5 pattern: resolve external data paths before command logic begins"

duration: ~5min
completed: 2026-03-20
---

# Phase 15 Plan 01: Slash Command Update Summary

**Added dynamic path resolution to /deliberate and /deliberate-code — both commands now work from any project directory.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~5 min |
| Completed | 2026-03-20 |
| Tasks | 3 completed |
| Files modified | 2 (+ 2 global copies) |
| Tests added | 0 (prompt-only changes, no code) |
| Total tests | 540 passed, 25 skipped |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Dynamic path resolution | Pass | Step 0.5 resolves paths via resolve_config_path/resolve_personas_dir |
| AC-2: Local override works | Pass | CWD files take priority in resolve chain |
| AC-3: Global copies updated | Pass | `diff` confirms global = project copies |
| AC-4: Custom persona discovery | Pass | PERSONAS_DIR parameterized in custom persona section |

## Accomplishments

- Both slash commands have "Step 0.5: Resolve Data Paths" preamble
- All `config.yaml` and `personas/` references parameterized as CONFIG_PATH and PERSONAS_DIR
- Global copies at `~/.claude/commands/` updated and verified
- Backward compatible: falls back to CWD paths if deliberators not installed

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `.claude/commands/deliberate.md` | Modified | Added Step 0.5, parameterized config/persona paths |
| `.claude/commands/deliberate-code.md` | Modified | Added Step 0.5, parameterized config/persona paths |
| `~/.claude/commands/deliberate.md` | Updated | Global copy matches project |
| `~/.claude/commands/deliberate-code.md` | Updated | Global copy matches project |

## Decisions Made

None — followed plan as specified.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

**Ready:**
- v0.5 milestone complete — all 3 phases done
- `/deliberate` and `/deliberate-code` work globally
- `uv tool install .` will produce a fully functional CLI

**Concerns:**
- None

**Blockers:**
- None

---
*Phase: 15-slash-command-update, Plan: 01*
*Completed: 2026-03-20*
