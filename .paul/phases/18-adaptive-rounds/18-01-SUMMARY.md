---
phase: 18-adaptive-rounds
plan: 01
subsystem: engine
tags: [convergence, adaptive-rounds, asyncio, subprocess, dataclass]

requires:
  - phase: 17-intake-fase
    provides: _call_functional_agent pattern, _parse_intake_output pattern

provides:
  - ConvergenceResult dataclass
  - Adaptive round loop (min_rounds / max_rounds)
  - _run_convergence_check() + _CONVERGENCE_SYSTEM_PROMPT
  - convergence_started / convergence_completed events
  - config.yaml max_rounds/min_rounds per preset

affects: [19-pool-expansion, 20-dynamic-team-selection]

tech-stack:
  added: []
  patterns: [functional-agent-reuse, structured-output-parsing, adaptive-loop]

key-files:
  created: []
  modified: [deliberators/models.py, deliberators/engine.py, deliberators/loader.py, deliberators/__main__.py, config.yaml, tests/test_models.py, tests/test_engine.py, tests/test_quality.py, tests/test_cli.py, tests/test_config.py, tests/test_loader.py]

key-decisions:
  - "min_rounds=1 default: every preset guarantees at least one analyst round"
  - "quick preset (min==max==1) never runs convergence check — no overhead"
  - "deep/code_deep upgraded to max_rounds=3 — payoff of adaptive architecture"
  - "Loader backward compat: reads 'rounds' as fallback for old config.yaml"

patterns-established:
  - "Functional agent reuse: _call_functional_agent() called from _run_convergence_check() verbatim"
  - "Structured output parsing: CONTINUE: yes/no + REASON: line → dataclass"
  - "Adaptive while loop: round_num < preset.max_rounds, convergence check between min and max"

duration: ~2h
started: 2026-03-22T00:00:00Z
completed: 2026-03-22T23:59:00Z
---

# Phase 18 Plan 01: Adaptive Rounds — Summary

**ConvergenceAgent replaces fixed round count: min/max bounds + structured yes/no judgment after each round**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~2h |
| Started | 2026-03-22 |
| Completed | 2026-03-22 |
| Tasks | 2 completed |
| Files modified | 15 |
| Commit | `6eecb11` |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: ConvergenceResult dataclass | Pass | frozen, should_continue/reason/round_number |
| AC-2: Preset model migration | Pass | rounds → max_rounds, min_rounds=1 default |
| AC-3: Convergence agent call | Pass | _run_convergence_check via _call_functional_agent |
| AC-4: Adaptive round loop (early stop) | Pass | min_rounds guaranteed, stops on "no" from convergence |
| AC-5: Max rounds respected | Pass | while loop capped at max_rounds |
| AC-6: Convergence events | Pass | convergence_started/completed with should_continue+reason |
| AC-7: CLI event display | Pass | "Convergentie check..." + result on stderr |
| AC-8: Config backward compat | Pass | quick(1/1), balanced(1/2), deep(1/3); loader fallback to 'rounds' |

## Accomplishments

- ConvergenceResult frozen dataclass added to models.py alongside Preset migration
- Adaptive while loop in engine.run(): min_rounds floor, convergence check between floor and ceiling, max_rounds hard cap
- _CONVERGENCE_SYSTEM_PROMPT + _parse_convergence_output + _run_convergence_check added to engine
- deep/code_deep upgraded from rounds=2 to max_rounds=3 — now capable of extra round when warranted
- 15 new tests added (TestConvergencePhase × 5, TestParseConvergenceOutput × 4, TestConvergenceResult × 2, event type tests)
- 622 tests pass total (was 607)

## Task Commits

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| Task 1 + Task 2 (combined) | `6eecb11` | feat | Phase 18 adaptive rounds — all files in one commit |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `deliberators/models.py` | Modified | ConvergenceResult dataclass; Preset max_rounds/min_rounds; convergence event types |
| `deliberators/engine.py` | Modified | _CONVERGENCE_SYSTEM_PROMPT, _parse_convergence_output, _run_convergence_check, adaptive loop |
| `deliberators/loader.py` | Modified | max_rounds with rounds fallback; min_rounds default 1; validate min <= max |
| `deliberators/__main__.py` | Modified | convergence_started/convergence_completed event printing |
| `config.yaml` | Modified | All 6 presets: rounds → max_rounds/min_rounds; deep/code_deep → max 3 |
| `tests/test_models.py` | Modified | TestConvergenceResult (2 tests), TestPreset updated, convergence event types |
| `tests/test_engine.py` | Modified | TestParseConvergenceOutput (4), TestConvergencePhase (5), index/count adjustments |
| `tests/test_quality.py` | Modified | Call index adjustments for convergence call insertion |
| `tests/test_cli.py` | Modified | Preset constructor: rounds=1 → max_rounds=1 |
| `tests/test_config.py` | Modified | max_rounds field references |
| `tests/test_loader.py` | Modified | max_rounds assertions, deep max_rounds=3 |
| `deliberators/context.py` | Modified | (prior-phase changes included in commit) |
| `deliberators/web_pusher.py` | Modified | (prior-phase changes included in commit) |
| `tests/test_context.py` | Modified | (prior-phase changes included in commit) |
| `tests/test_web_pusher.py` | Created | (prior-phase changes included in commit) |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Tasks 1+2 committed together | All changes were in-progress from prior session | Single clean commit for the phase |
| deep/code_deep max_rounds=3 | Adaptive rounds make the extra round economical — stops early if converged | Deep preset now more capable |
| min_rounds=1 default | Every preset must guarantee at least one round; convergence check is between min and max, never before min | Simple, correct semantics |
| quick preset: min==max==1 | No convergence overhead for quick presets | Zero cost for quick runs |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 3 | Stale .rounds refs in test files not in plan's files_modified list |
| Scope additions | 0 | — |
| Deferred | 0 | — |

**Total impact:** Minor auto-fixes, no scope creep

### Auto-fixed Issues

**1. Stale Preset(.rounds=...) in tests not listed in plan**
- **Found during:** Task 2 (test run)
- **Issue:** tests/test_loader.py and tests/test_cli.py had `Preset(..., rounds=1)` which broke after models.py migration
- **Fix:** Changed to `max_rounds=1` in both files
- **Verification:** `uv run pytest` 622 passed

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Call indices in test_engine/test_quality shifted by +1 | Convergence call inserted at index 6 (between R1 and R2) — updated all slice indices |
| `uv run pytest` "No such file or directory" | Used `uv run python -m pytest` instead |

## Next Phase Readiness

**Ready:**
- Preset.max_rounds/min_rounds established — Phase 19 can add new personas without touching this
- Adaptive loop stable — Phase 20 dynamic team selection builds on top of this
- _call_functional_agent pattern proven twice (intake + convergence) — ready for Phase 20 team assembler

**Concerns:**
- None — Phase 18 is self-contained

**Blockers:**
- None

---
*Phase: 18-adaptive-rounds, Plan: 01*
*Completed: 2026-03-22*
