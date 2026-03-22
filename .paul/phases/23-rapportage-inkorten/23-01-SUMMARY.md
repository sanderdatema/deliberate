---
phase: 23-rapportage-inkorten
plan: 01
subsystem: formatter, cli, engine, commands
tags: [verbose-flag, report-length, synthesis-conciseness]

requires:
  - phase: 22-rapportage-redesign
    provides: thematic formatter with per-persona appendix
provides:
  - Volledig Verslag appendix hidden by default, shown with --verbose
  - Synthesis prompt with conciseness constraints
  - Compact slash command output format
affects: []

tech-stack:
  added: []
  patterns: [verbose-opt-in-appendix]

key-files:
  created: []
  modified: [deliberators/formatter.py, deliberators/__main__.py, deliberators/engine.py, .claude/commands/deliberate.md, tests/test_cli.py]

key-decisions:
  - "Appendix is opt-in via verbose parameter, not removed entirely"
  - "Slash command always shows compact format (no --verbose equivalent)"

patterns-established:
  - "verbose=False default on format() — callers must opt in for full output"

duration: ~15min
started: 2026-03-22T00:00:00Z
completed: 2026-03-22T23:59:00Z
---

# Phase 23 Plan 01: Rapportage Inkorten Summary

**Default rapport output drastisch verkort: Volledig Verslag appendix achter --verbose flag, synthese-prompt met beknoptheidsconstraints**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~15min |
| Started | 2026-03-22 |
| Completed | 2026-03-22 |
| Tasks | 4 completed |
| Files modified | 5 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Default output bevat GEEN Volledig Verslag | Pass | `_format_thematic()` skips appendix when `verbose=False` |
| AC-2: --verbose flag toont Volledig Verslag | Pass | CLI arg + `format(result, verbose=True)` includes appendix |
| AC-3: Slash command Step 8 compact | Pass | Volledig Verslag removed from template, note added |
| AC-4: Synthesis prompt beknoptheid | Pass | Max 800 words, bullet points, 3-4 paragraphs per section |
| AC-5: Alle tests passen | Pass | 1166 passed, 0 failed, 54 skipped |

## Accomplishments

- `_format_thematic()` now takes `verbose` kwarg — appendix only rendered when True
- `--verbose` CLI flag added to `build_parser()`, passed through to formatter
- Synthesis prompt updated with explicit conciseness constraints (max 800 words, bullet lists, 3-4 tensions max)
- Slash command Step 8 simplified to compact format only

## Task Commits

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| Task 1-4 | pending | feat | --verbose flag + compact output + synthesis constraints |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `deliberators/formatter.py` | Modified | `verbose` kwarg on `format()` and `_format_thematic()`; appendix gated |
| `deliberators/__main__.py` | Modified | `--verbose` argument + pass-through to formatter |
| `deliberators/engine.py` | Modified | `_SYNTHESIS_SYSTEM_PROMPT` with conciseness constraints |
| `.claude/commands/deliberate.md` | Modified | Step 8 compact format, no Volledig Verslag |
| `tests/test_cli.py` | Modified | 4 tests updated + 2 new tests (verbose flag parsing, verbose appendix) |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| verbose as keyword-only arg | Prevents accidental positional use, clear intent | Clean API |
| Slash command always compact | No way to pass --verbose in slash command context | Consistent short output |
| 800 word max in synthesis prompt | Enough for substance, prevents verbosity | Shorter reports |

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| pytest uninstalled after `uv sync` (missing `--extra dev`) | Re-ran with `uv sync --extra dev` |

## Next Phase Readiness

**Ready:**
- Phase 24 (Robuustheid) can proceed — no dependencies on this phase
- Report output now compact by default

**Concerns:**
- Synthesis quality depends on LLM following word limits (soft constraint)

**Blockers:**
- None

---
*Phase: 23-rapportage-inkorten, Plan: 01*
*Completed: 2026-03-22*
