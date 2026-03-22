---
phase: 17-intake-fase
plan: 01
subsystem: engine
tags: [intake, functional-agent, clarification, subprocess, dataclass]

requires:
  - phase: 16-persona-model-routing
    provides: config.model as fallback for functional agents without Persona

provides:
  - IntakeBrief dataclass
  - _run_intake() with max-3 clarification loop
  - _call_functional_agent() for persona-less subprocess calls
  - INTAKE CONTEXT injected into all analyst prompts

affects: phase-18-adaptive, phase-20-rapportage

tech-stack:
  added: []
  patterns: [functional-agent via _call_functional_agent, structured output parsing]

key-files:
  created: []
  modified: [deliberators/models.py, deliberators/engine.py, deliberators/__main__.py, tests/test_models.py, tests/test_engine.py, tests/test_quality.py]

key-decisions:
  - "Intake skipped for code_* presets: code review has different flow"
  - "_call_functional_agent separate from _subprocess_call: cleaner interface, no Persona dependency"
  - "_parse_intake_output with fallback: graceful degradation if LLM ignores format"
  - "on_clarify callback guards: empty string return = skip clarification silently"

patterns-established:
  - "Functional agents use _call_functional_agent(system_prompt, prompt, model)"
  - "Structured LLM output parsed with line-by-line key: value scanner + fallback"
  - "Test index offset: intake adds call[0], analyst calls shift by +1"

duration: 60min
started: 2026-03-22T13:00:00Z
completed: 2026-03-22T14:00:00Z
---

# Phase 17 Plan 01: Intake Fase Summary

**Functional intake agent analyses question clarity before analyst rounds; produces IntakeBrief injected into all analyst prompts; max-3 clarification loop via on_clarify callback.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~60 min |
| Started | 2026-03-22 |
| Completed | 2026-03-22 |
| Tasks | 3/3 completed |
| Files modified | 6 |
| Tests | 607 passed (+17 new) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: IntakeBrief dataclass | Pass | question, summary, clarifications, is_clear |
| AC-2: Functional intake subprocess (no Persona) | Pass | _call_functional_agent uses config.model |
| AC-3: Clarification loop max 3 | Pass | Verified by test_clarification_max_three_rounds |
| AC-4: Skippable when on_clarify=None | Pass | Returns brief with is_clear=False |
| AC-5: Intake brief in analyst prompt | Pass | INTAKE CONTEXT: before QUESTION FOR DELIBERATION: |
| AC-6: intake events in DeliberationEvent | Pass | intake_started / intake_completed emitted |
| AC-7: intake_brief in DeliberationResult | Pass | result.intake_brief is non-None for non-code presets |
| AC-8: CLI integration | Pass | on_clarify via stdin with isatty guard |

## Accomplishments

- Intake agent runs before every non-code deliberation; analysts now share a common frame (what the question really asks, assumptions, dimensions)
- `_call_functional_agent()` establishes the pattern for all future functional agents (Phase 18 convergence agent will reuse it)
- Structured output parser with fallback makes intake robust against LLM format drift
- 17 new tests covering all AC scenarios including clarification loop edge cases

## Task Commits

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| All 3 tasks | `9a7dd73` | feat | Intake fase — functional agent + tests |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `deliberators/models.py` | Modified | IntakeBrief dataclass + intake event types |
| `deliberators/engine.py` | Modified | _run_intake, _call_functional_agent, _parse_intake_output, on_clarify |
| `deliberators/__main__.py` | Modified | intake event printing, on_clarify via stdin |
| `tests/test_models.py` | Modified | TestIntakeBrief + intake event type tests |
| `tests/test_engine.py` | Modified | TestIntakePhase (7 tests) + TestParseIntakeOutput (4 tests) + index fixes |
| `tests/test_quality.py` | Modified | Index offsets fixed for intake (+1) |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Skip intake for code_* presets | Code review has different clarity needs; intake designed for open questions | code_quick/balanced/deep unaffected |
| _call_functional_agent separate from _subprocess_call | No Persona dependency; cleaner for convergence agent (Phase 18) reuse | Pattern established for all functional agents |
| Structured output parsing with fallback | LLM occasionally ignores format; fallback prevents silent failures | Robust even on format drift |

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| test_engine.py + test_quality.py index offsets | Intake adds call[0]; analyst calls shift +1. Fixed 9 assertions across both files |

## Next Phase Readiness

**Ready:**
- `_call_functional_agent()` pattern ready for ConvergenceAgent (Phase 18)
- `IntakeBrief` available in DeliberationResult for convergence context
- `intake_brief` flows through `_run_analyst_round` → `_build_analyst_prompt`

**Concerns:**
- None

**Blockers:**
- None — Phase 18 (Adaptive Rounds) can proceed

---
*Phase: 17-intake-fase, Plan: 01*
*Completed: 2026-03-22*
