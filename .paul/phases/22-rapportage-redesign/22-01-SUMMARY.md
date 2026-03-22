---
phase: 22-rapportage-redesign
plan: 01
subsystem: engine, formatter, cli, commands
tags: [thematic-report, synthesis-agent, rapportage, appendix]

requires:
  - phase: 18-adaptive-rounds
    provides: convergence info, multi-round data
  - phase: 21-decision-memory
    provides: DecisionRecord for action items structure

provides:
  - Synthesis functional agent generates thematic report sections
  - Thematic formatter (landschap, spanningsvelden, blinde vlekken, verschuiving, actiepunten)
  - Per-persona output preserved in "Volledig Verslag" appendix
  - Fallback to legacy per-persona format when synthesis absent
affects: []

tech-stack:
  added: []
  patterns: [synthesis-agent, thematic-formatter-with-appendix]

key-files:
  created: []
  modified: [deliberators/engine.py, deliberators/formatter.py, tests/test_cli.py, tests/test_engine.py, tests/test_quality.py, .claude/commands/deliberate.md, CLAUDE.md]

key-decisions:
  - "Synthesis is a single functional agent call, not multi-agent pipeline"
  - "Per-persona output moved to appendix, not removed"
  - "Fallback to legacy format if synthesis_output is None"
  - "Appendix uses ### and #### headers (demoted from ## and ###) to nest under Volledig Verslag"

patterns-established:
  - "Thematic report pattern: synthesis sections first, per-persona appendix last"
  - "Graceful degradation: no synthesis → legacy format, never crash"

duration: ~20min
started: 2026-03-22T00:00:00Z
completed: 2026-03-22T23:59:00Z
---

# Phase 22 Plan 01: Rapportage Redesign Summary

**Synthesis agent generates thematic report (landschap, spanningsvelden, blinde vlekken, verschuiving, actiepunten); per-persona output preserved in Volledig Verslag appendix**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~20min |
| Started | 2026-03-22 |
| Completed | 2026-03-22 |
| Tasks | 2 completed |
| Files modified | 7 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Thematic report structure | Pass | Kort & Concreet → title → thematic sections → Volledig Verslag appendix |
| AC-2: Synthesis agent generates thematic sections | Pass | _run_synthesis() calls functional agent after editorial, stores on result.synthesis_output |
| AC-3: Per-persona output preserved in appendix | Pass | _render_per_persona_body() used by both thematic and fallback formats |
| AC-4: Slash command updated | Pass | Steps 7+8 rewritten for thematic format, hardcoded persona names removed |
| AC-5: All tests pass | Pass | 1163 passed, 0 failed, 54 skipped |

## Accomplishments

- _SYNTHESIS_SYSTEM_PROMPT and _run_synthesis() as 4th functional agent in pipeline
- ResultFormatter rewritten with _format_thematic() and _format_per_persona() (fallback)
- Per-persona output demoted to appendix with ### and #### headers
- 2 new formatter tests (thematic sections, fallback without synthesis)
- Agent count assertions updated across test_engine.py and test_quality.py

## Task Commits

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| Task 1 + Task 2 | pending | feat | Synthesis agent + thematic formatter + slash command update |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `deliberators/engine.py` | Modified | _SYNTHESIS_SYSTEM_PROMPT, _run_synthesis(), synthesis_output on DeliberationResult |
| `deliberators/formatter.py` | Modified | Thematic report with per-persona appendix, fallback to legacy |
| `tests/test_cli.py` | Modified | Thematic sections test, appendix test, fallback test |
| `tests/test_engine.py` | Modified | Agent count +1 synthesis (3 assertions) |
| `tests/test_quality.py` | Modified | Call indices adjusted for synthesis agent |
| `.claude/commands/deliberate.md` | Modified | Steps 7+8 rewritten for thematic format |
| `CLAUDE.md` | Modified | Architecture docs updated |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Single synthesis agent call | Multi-agent pipeline would be over-engineering for report generation | Simple, fast, one API call |
| Appendix with demoted headers | ### Ronde and #### Analyst nest cleanly under ## Volledig Verslag | Clean hierarchy |
| Fallback to legacy format | Tests with mock subprocess return empty synthesis | Never crashes, graceful degradation |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 3 | Agent count and call index assertions in test_engine.py and test_quality.py |
| Scope additions | 0 | — |
| Deferred | 0 | — |

**Total impact:** 3 auto-fixes for existing test assertions that needed +1 for synthesis agent call

### Auto-fixed Issues

**1. Agent count assertions (test_engine.py)**
- **Found during:** Full test suite run
- **Issue:** 3 assertions expected N agents but synthesis adds +1
- **Fix:** Updated counts: 6→7, 16→17, 6→7

**2. Quality test call indices (test_quality.py)**
- **Found during:** Full test suite run
- **Issue:** tracker.calls[1:], calls[12:], calls[-1] now include synthesis call
- **Fix:** Adjusted to calls[1:-1], calls[12:-1], calls[-2]

**3. Code context test (test_engine.py)**
- **Found during:** Full test suite run
- **Issue:** calls[4:] included synthesis which doesn't get code context
- **Fix:** Changed to calls[4:-1] to exclude synthesis

## Next Phase Readiness

**Ready:**
- v0.6 milestone complete — all 7 phases shipped
- Full pipeline: intake → team selection → analyst rounds → convergence → editorial → synthesis → auto-save

**Concerns:**
- Synthesis quality depends on LLM output structure matching expected ## headers
- No streaming of synthesis to web viewer

**Blockers:**
- None

---
*Phase: 22-rapportage-redesign, Plan: 01*
*Completed: 2026-03-22*
