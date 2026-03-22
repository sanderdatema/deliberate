---
phase: 19-pool-expansion
plan: 02
subsystem: personas
tags: [persona, yaml, pool-expansion, gender-diversity, cross-domain]

requires:
  - phase: 19-pool-expansion
    provides: domains field on Persona dataclass, schema, loader validation
  - phase: 16-persona-model-routing
    provides: model field and PersonaLoader validation pattern

provides:
  - 29 new analyst personas across 15+ expertise domains
  - Pool expanded from 25 to 54 personas (49 analysts, 5 editors)
  - Gender distribution 23F/28M/3N (43%/52%/5%)
affects: [20-dynamic-team-selection]

tech-stack:
  added: []
  patterns: [persona-kernvraag-driven-prompts, cross-domain-expertise-tagging]

key-files:
  created: ["personas/*.yaml (29 new)", "deliberators/data/personas/*.yaml (29 bundled)"]
  modified: [tests/test_personas.py, tests/test_loader.py, tests/test_package.py]

key-decisions:
  - "All new personas are analysts with model: sonnet (cost-efficient)"
  - "Each persona's system_prompt driven by unique kernvraag from RESEARCH.md"
  - "Test counts updated in 3 test files (test_personas, test_loader, test_package)"

patterns-established:
  - "Persona kernvraag pattern: each persona has one core question that drives all analysis"
  - "reasoning_style in Dutch, system_prompt in English (matching existing convention)"

duration: ~20min
started: 2026-03-22T00:00:00Z
completed: 2026-03-22T23:59:00Z
---

# Phase 19 Plan 02: Pool Expansion — 29 New Personas Summary

**29 new analyst personas created spanning psychology, governance, rhetoric, systems thinking, ethics, mathematics, and more — pool grows from 25 to 54**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~20min |
| Started | 2026-03-22 |
| Completed | 2026-03-22 |
| Tasks | 2 completed |
| Files created | 58 (29 source + 29 bundled) |
| Files modified | 3 (test count assertions) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: All 29 new persona files exist | Pass | 54 total persona YAMLs in personas/ |
| AC-2: Every new persona conforms to schema | Pass | All required fields present, model=sonnet, role=analyst, domains valid |
| AC-3: Persona system_prompts substantial and unique | Pass | All >= 50 words, FORBIDDEN/MUST NOT + FORMAT YOUR RESPONSE present |
| AC-4: Test counts updated | Pass | 54 total, 49 analysts, 5 editors in test_personas, test_loader, test_package |
| AC-5: Bundled data synced | Pass | 54 personas in deliberators/data/personas/ |
| AC-6: All tests pass | Pass | 1169 passed, 0 failed |

## Accomplishments

- 29 unique personas with kernvraag-driven system_prompts across 15+ domains
- Gender balance achieved: 43% female, 52% male, 5% non-binary
- 1169 tests pass (+493 from new parametrized persona tests)
- Phase 20 has a broad, domain-tagged pool ready for dynamic team selection

## Task Commits

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| Task 1 + Task 2 | pending | feat | 29 personas + test count updates + bundled sync |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `personas/*.yaml` (29 new) | Created | New analyst personas |
| `deliberators/data/personas/*.yaml` (29 new) | Created | Bundled copies |
| `tests/test_personas.py` | Modified | Count: 25→54, 20→49 |
| `tests/test_loader.py` | Modified | Count: 25→54, 20→49 |
| `tests/test_package.py` | Modified | Bundled count: 25→54 |

## New Personas

### Women (14)
Joan Clarke, Margaret Hamilton, Barbara Liskov, Hedy Lamarr, Ada Lovelace, Lynn Conway, Radia Perlman, Frances Allen, Maryam Mirzakhani, Katherine Johnson, Donella Meadows, Elinor Ostrom, Cecilia Payne-Gaposchkin, Virginia Apgar

### Men (10)
Alan Turing, Daniel Kahneman, Nassim Nicholas Taleb, Johan Rudolf Thorbecke, William Shakespeare, Aristoteles, Marcus Tullius Cicero, John Rawls, Buckminster Fuller, Arsene Lupin (returning)

### Fictional Characters (5)
Odysseus, Scheherazade, Portia, Atticus Finch, Elizabeth Bennet

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| All 29 use model: sonnet | Cost-efficient for analysts; Opus reserved for editors/synthesis | ~50% cost savings on new personas |
| Test counts in 3 files | test_loader and test_package also had hardcoded counts | Auto-fix during verification |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | test_loader.py and test_package.py also had count assertions |
| Scope additions | 0 | — |
| Deferred | 0 | — |

**Total impact:** One auto-fix (additional test count updates), no scope creep

### Auto-fixed Issues

**1. Additional test count assertions**
- **Found during:** Task 2 verify (test suite run)
- **Issue:** test_loader.py (lines 35, 70) and test_package.py (line 40) also had hardcoded persona counts
- **Fix:** Updated all three to 54/49 counts
- **Verification:** 1169 tests pass

## Next Phase Readiness

**Ready:**
- Phase 20 has 54 domain-tagged personas to select from
- Intake agent can match question topics to persona domains
- Gender-balanced pool enables balanced team selection

**Concerns:**
- Bundled data sync remains manual (cp personas/*.yaml deliberators/data/personas/)

**Blockers:**
- None

---
*Phase: 19-pool-expansion, Plan: 02*
*Completed: 2026-03-22*
