---
phase: 19-pool-expansion
plan: 01
subsystem: personas
tags: [domains, persona, loader, dataclass, yaml]

requires:
  - phase: 16-persona-model-routing
    provides: Persona dataclass with model field; PersonaLoader validation pattern

provides:
  - domains field on Persona dataclass
  - domains validation in PersonaLoader
  - domains in schema.yaml
  - all 25 existing personas tagged with domain expertise
affects: [20-dynamic-team-selection]

tech-stack:
  added: []
  patterns: [persona-domain-tagging, snake_case-taxonomy]

key-files:
  created: []
  modified: [deliberators/models.py, deliberators/loader.py, personas/schema.yaml, "personas/*.yaml (all 25)", "deliberators/data/personas/*.yaml (bundled sync)"]

key-decisions:
  - "Free-form string tags, not enum — intake agent does semantic matching in Phase 20"
  - "2-5 domains per persona based on RESEARCH.md expertise matrix"
  - "Bundled data/personas/ synced from personas/ via cp — no separate tooling"

patterns-established:
  - "Domains taxonomy: lowercase_snake_case, test-enforced via regex"
  - "Bundled personas must always be synced with source personas/"

duration: ~30min
started: 2026-03-22T00:00:00Z
completed: 2026-03-22T23:59:00Z
---

# Phase 19 Plan 01: Pool Expansion — Schema Migration Summary

**domains field added to Persona dataclass, loader, schema, and all 25 existing persona YAMLs**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~30min |
| Started | 2026-03-22 |
| Completed | 2026-03-22 |
| Tasks | 2 completed |
| Files modified | 57 |
| Commit | `eaee000` |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Persona dataclass has domains | Pass | `domains: tuple[str, ...]` field added |
| AC-2: Schema requires domains | Pass | required_fields + domains_constraints in schema.yaml |
| AC-3: Loader reads domains | Pass | tuple(domains) in Persona constructor |
| AC-4: Loader rejects missing/empty domains | Pass | PersonaLoadError raised |
| AC-5: All 25 personas have domains | Pass | 2-5 tags per persona |
| AC-6: Consistent with expertise matrix | Pass | Schneier+Clarke→security, Linus+Beck+Fowler→code_quality/software_design |

## Accomplishments

- Persona.domains field established as the Phase 20 team-selection foundation
- 676 tests pass (+54 new domains validation tests)
- Domain taxonomy defined: lowercase_snake_case, 20+ domain categories
- Both source personas/ and bundled deliberators/data/personas/ updated

## Task Commits

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| Task 1 + Task 2 (combined) | `eaee000` | feat | All 57 files in one commit |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `deliberators/models.py` | Modified | `domains: tuple[str, ...]` added to Persona |
| `deliberators/loader.py` | Modified | REQUIRED_PERSONA_FIELDS + domains validation |
| `personas/schema.yaml` | Modified | domains in required_fields + constraints |
| `personas/*.yaml` (25 files) | Modified | domains field added to each |
| `deliberators/data/personas/*.yaml` (25) | Modified | bundled copies synced |
| `tests/test_models.py` | Modified | domains in constructors + test_domains_field |
| `tests/test_loader.py` | Modified | domains in test data + 3 validation tests |
| `tests/test_personas.py` | Modified | domains in REQUIRED_FIELDS + 2 validation tests per persona |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Free-form string tags | Semantic matching by intake agent; no enum needed | Phase 20 uses substring/embedding match |
| Bundled sync via cp | No tooling overhead; bundled data is a copy of source | Must remember to sync after persona changes |
| domains not consumed by engine yet | Phase 20 handles consumption | Zero behavioral change in this plan |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Bundled data/personas/ also needed sync |
| Scope additions | 0 | — |
| Deferred | 0 | — |

**Total impact:** One auto-fix, no scope creep

### Auto-fixed Issues

**1. Bundled personas missing domains**
- **Found during:** Task 2 verify (`test_package.py::test_bundled_personas_are_loadable` failed)
- **Issue:** `deliberators/data/personas/` is a bundled copy used as fallback; same loader, same validation
- **Fix:** `cp personas/*.yaml deliberators/data/personas/`
- **Verification:** 676 tests pass

## Next Phase Readiness

**Ready:**
- Phase 20 can read `persona.domains` for team selection
- Domain taxonomy established and test-enforced (snake_case regex)
- Plan 02 (29 new personas) can use same YAML structure

**Concerns:**
- Bundled data sync is manual — if personas change, remember to cp again

**Blockers:**
- None

---
*Phase: 19-pool-expansion, Plan: 01*
*Completed: 2026-03-22*
