---
phase: 07-code-personas
plan: 01
subsystem: personas
tags: [yaml, code-review, personas, presets]

requires:
  - phase: 06-integration-polish
    provides: persona schema, config structure, test suite
provides:
  - 9 code-review analyst personas (Linus, Kent Beck, Fowler, Schneier, Jobs, Don Norman, Jony Ive, Christensen, Hopper)
  - 1 code-review editor persona (Code Synthesizer)
  - 3 code-mode presets (code_quick, code_balanced, code_deep)
affects: [08-code-context-pipeline, 09-code-integration]

tech-stack:
  added: []
  patterns: [code-specific forbidden constraints, developer-as-user perspective in personas]

key-files:
  created:
    - personas/linus.yaml
    - personas/kent-beck.yaml
    - personas/fowler.yaml
    - personas/schneier.yaml
    - personas/jobs.yaml
    - personas/don-norman.yaml
    - personas/jony-ive.yaml
    - personas/christensen.yaml
    - personas/hopper.yaml
    - personas/code-synthesizer.yaml
  modified:
    - config.yaml
    - deliberators/loader.py
    - tests/test_personas.py
    - tests/test_config.py
    - tests/test_loader.py

key-decisions:
  - "Code Synthesizer as sole code editor: single synthesizer instead of multiple editorial perspectives"
  - "Code presets use underscore naming (code_quick) to coexist with existing presets"

patterns-established:
  - "Code personas use same schema as deliberation personas — no schema changes needed"
  - "Each code persona targets a distinct review dimension with no overlap"

duration: ~10min
started: 2026-03-18T19:00:00Z
completed: 2026-03-18T19:10:00Z
---

# Phase 7 Plan 01: Code Personas Summary

**9 code-review analyst personas + 1 code editor + 3 code presets, all passing 478 tests**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~10 min |
| Tasks | 2 completed |
| Files created | 10 |
| Files modified | 5 |
| Tests | 478 passed, 25 skipped |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Code Analyst Personas Valid | Pass | All 9 analysts pass schema validation |
| AC-2: Code Editor Persona Valid | Pass | code-synthesizer.yaml passes as editor |
| AC-3: Each Persona Has Unique Code Focus | Pass | 9 distinct dimensions: quality, TDD, architecture, security, product, UX, craft, JTBD, pragmatism |
| AC-4: Code Presets in Config | Pass | code_quick/balanced/deep all valid, correct sizing |
| AC-5: All Tests Pass | Pass | 478 passed, 0 failed |

## Accomplishments

- Created 9 code analyst personas each targeting a distinct code-review dimension
- Created Code Synthesizer editor that integrates analyst perspectives into prioritized action items
- Added 3 code presets (code_quick: 3+1, code_balanced: 5+1, code_deep: 9+1)
- Updated STANDARD_PERSONAS in loader.py so engine recognizes new personas
- All existing tests continue to pass — no regressions

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `personas/linus.yaml` | Created | Code purist — simplicity, no-nonsense |
| `personas/kent-beck.yaml` | Created | TDD/simplicity — testability, YAGNI |
| `personas/fowler.yaml` | Created | Architecture — code smells, refactoring |
| `personas/schneier.yaml` | Created | Security — threat models, OWASP |
| `personas/jobs.yaml` | Created | Product vision — user impact |
| `personas/don-norman.yaml` | Created | UX — API ergonomics, error messages |
| `personas/jony-ive.yaml` | Created | Design craft — consistency, naming |
| `personas/christensen.yaml` | Created | JTBD — user-fit, over/under-serving |
| `personas/hopper.yaml` | Created | Pragmatism — shipping, trade-offs |
| `personas/code-synthesizer.yaml` | Created | Code review synthesis editor |
| `config.yaml` | Modified | Added code_quick/balanced/deep presets |
| `deliberators/loader.py` | Modified | Added 10 new names to STANDARD_PERSONAS |
| `tests/test_personas.py` | Modified | Updated persona counts (15→25, 11→20, 4→5) |
| `tests/test_config.py` | Modified | Added code preset tests (TestCodePresets class) |
| `tests/test_loader.py` | Modified | Updated counts and preset expectations |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Single code editor (Code Synthesizer) | Code review needs one actionable synthesis, not multiple editorial layers | Simpler preset composition |
| Underscore naming for code presets | `code_quick` vs `code-quick` matches YAML key conventions | Consistent with existing preset naming |
| No schema changes | Existing schema supports code personas as-is | Zero impact on v0.1/v0.2 functionality |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Essential — loader needed updating |
| Scope additions | 0 | — |
| Deferred | 0 | — |

**Total impact:** Minimal — one necessary file (loader.py) not listed in original plan.

### Auto-fixed Issues

**1. STANDARD_PERSONAS in loader.py**
- **Found during:** Task 1 verification (test_loader.py failures)
- **Issue:** New personas not in STANDARD_PERSONAS frozenset → discover_custom treated them as custom, count assertions failed
- **Fix:** Added 10 new persona names to STANDARD_PERSONAS in deliberators/loader.py
- **Verification:** All 478 tests pass

## Issues Encountered

None

## Next Phase Readiness

**Ready:**
- 10 code personas available for Phase 8 (Code Context Pipeline)
- 3 code presets ready for Phase 9 (Code Integration & Command)
- Existing engine can already load and use new personas

**Concerns:**
- None

**Blockers:**
- None

---
*Phase: 07-code-personas, Plan: 01*
*Completed: 2026-03-18*
