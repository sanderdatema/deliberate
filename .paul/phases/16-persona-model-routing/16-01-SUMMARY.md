---
phase: 16-persona-model-routing
plan: 01
subsystem: personas
tags: [model-routing, personas, yaml, dataclass, subprocess]

requires:
  - phase: 15-global-install
    provides: bundled data in deliberators/data/, fallback loader chain

provides:
  - Per-persona model routing (opus/sonnet per YAML field)
  - Machiavelli persona (replaces Lupin)
  - Knuth persona (replaces Christensen)
  - Jony Ive redefined to UI/UX reviewer
  - All 25 persona YAMLs with model field

affects: phase-17-intake, phase-18-adaptive, phase-20-rapportage

tech-stack:
  added: []
  patterns: [per-persona model routing via YAML field + dataclass field]

key-files:
  created: [personas/machiavelli.yaml, personas/knuth.yaml]
  modified: [deliberators/models.py, deliberators/loader.py, deliberators/engine.py, personas/schema.yaml, config.yaml, all 23 other persona YAMLs]

key-decisions:
  - "Jony Ive redefined: UI/UX for what users SEE (not code formatting — Linus' domain)"
  - "Machiavelli as Lupin replacement: strategic realist with strong character-function alignment"
  - "Knuth on sonnet: structured pattern matching fits performance analysis"
  - "Config.model kept as fallback for functional agents (intake, convergence) without persona"

patterns-established:
  - "Persona YAML must declare model: opus|sonnet explicitly (no default)"
  - "PersonaLoader validates model against VALID_MODELS tuple"
  - "Engine passes persona.model to --model flag; config.model is functional-agent fallback"

duration: 90min
started: 2026-03-22T10:00:00Z
completed: 2026-03-22T12:00:00Z
---

# Phase 16 Plan 01: Persona Audit + Per-Persona Model Routing Summary

**Per-persona model routing implemented across all 25 YAMLs; Lupin→Machiavelli, Christensen→Knuth, Ive redefined to UI/UX reviewer; ~50% cost reduction on analyst-heavy presets.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~90 min |
| Started | 2026-03-22 |
| Completed | 2026-03-22 |
| Tasks | All completed |
| Files modified | 68 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: model field in Persona dataclass | Pass | `model: str` after `name`, before `role` |
| AC-2: PersonaLoader validates model | Pass | Raises PersonaLoadError for haiku/invalid |
| AC-3: Engine uses persona.model | Pass | `_subprocess_call` uses `persona.model or self.config.model` |
| AC-4: schema.yaml updated | Pass | model field added with model_values: [opus, sonnet] |
| AC-5: Machiavelli created, Lupin removed | Pass | personas/machiavelli.yaml, lupin.yaml deleted |
| AC-6: Knuth created, Christensen removed | Pass | personas/knuth.yaml, christensen.yaml deleted |
| AC-7: Jony Ive redefined to UI/UX | Pass | Full rewrite — visual hierarchy, accessibility, interaction |
| AC-8: All 25 YAMLs have model field | Pass | opus/sonnet per audit table |
| AC-9: config.yaml presets updated | Pass | quick/balanced/deep use machiavelli; code_deep uses knuth |
| AC-10: All tests pass | Pass | 590 passed, 25 skipped |

## Accomplishments

- All 25 persona YAMLs now declare `model: opus|sonnet` explicitly; ~50% of analysts on sonnet reduces cost significantly on multi-analyst presets
- Persona swap: Lupin (weak character-function fit) → Machiavelli (strategic realist, strong fit); Christensen (product disruption) → Knuth (algorithmic performance analyst)
- Jony Ive corrected from "code craft" (overlapped Linus) to "UI/UX design reviewer" — fills a genuine gap: what end users see was underrepresented
- Full vertical slice: schema → dataclass → loader → YAMLs → config → engine → tests

## Task Commits

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| All tasks (single commit) | `08a50d6` | feat | v0.6 persona audit + per-persona model routing |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `personas/machiavelli.yaml` | Created | Strategic realist analyst (replaces Lupin) |
| `personas/knuth.yaml` | Created | Algorithmic performance analyst (replaces Christensen) |
| `personas/jony-ive.yaml` | Modified | Full rewrite: UI/UX reviewer (visual, a11y, interaction) |
| `personas/lupin.yaml` | Deleted | Replaced by Machiavelli |
| `personas/christensen.yaml` | Deleted | Replaced by Knuth |
| `personas/*.yaml` (23 files) | Modified | Added `model: opus\|sonnet` field |
| `personas/schema.yaml` | Modified | Added model field + model_values enum |
| `deliberators/models.py` | Modified | Added `model: str` field to Persona dataclass |
| `deliberators/loader.py` | Modified | VALID_MODELS constant + validation in PersonaLoader |
| `deliberators/engine.py` | Modified | `_subprocess_call` uses `persona.model` |
| `config.yaml` | Modified | Preset compositions updated |
| `deliberators/data/*` | Modified | Bundled copies synced |
| `tests/test_personas.py` | Modified | model field added to REQUIRED_FIELDS, test_model_is_valid |
| `tests/test_loader.py` | Modified | test_missing_model_raises, test_invalid_model_raises |
| `tests/test_engine.py` | Modified | test_model_passed_from_persona, test_mixed_models |
| `tests/test_models.py` | Modified | model arg added to all Persona constructions |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Jony Ive → UI/UX (not code craft) | "Code craft" overlapped Linus; UI/UX is genuinely underrepresented | code_deep preset now covers visual, accessibility, interaction |
| Config.model kept as fallback | Functional agents (intake, convergence) won't have persona objects | Phases 17+18 can use config.model for their agents |
| Machiavelli on opus | Nuanced strategic reasoning benefits from Opus | Higher quality on incentive/power dynamics analysis |
| Knuth on sonnet | Structured pattern matching (Big-O, data structures) fits Sonnet | Cost reduction without quality loss |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | test_models.py missing model arg |
| Scope additions | 0 | — |
| Deferred | 0 | — |

**Total impact:** One test fix discovered during execution, no scope creep.

### Auto-fixed Issues

**1. test_models.py Persona constructor missing model arg**
- **Found during:** Test run after implementation
- **Issue:** All three Persona() constructions in test_models.py lacked `model=` argument after dataclass field added
- **Fix:** Added `model="opus"` or `model="sonnet"` to all three test cases
- **Verification:** 590 tests pass

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| None | — |

## Next Phase Readiness

**Ready:**
- `Persona.model` available throughout engine for all agents
- `config.model` still available as fallback for functional agents (Phase 17/18)
- All presets validated with new persona composition
- Bundled data synced

**Concerns:**
- None

**Blockers:**
- None — Phase 17 (Intake) can proceed

---
*Phase: 16-persona-model-routing, Plan: 01*
*Completed: 2026-03-22*
