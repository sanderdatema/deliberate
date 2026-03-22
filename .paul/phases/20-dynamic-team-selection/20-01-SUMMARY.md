---
phase: 20-dynamic-team-selection
plan: 01
subsystem: engine, models, cli, commands
tags: [team-selection, intake, unified-command, cross-domain, gender-balance]

requires:
  - phase: 19-pool-expansion
    provides: 54 domain-tagged personas with domains field
  - phase: 17-intake-fase
    provides: _call_functional_agent() pattern, IntakeBrief dataclass

provides:
  - TeamSelectionAgent functional agent selects optimal team from 54-persona pool
  - Unified /deliberate command replacing /deliberate and /deliberate-code
  - Preset model with team_size/editor_count instead of fixed analyst/editor lists
  - Cross-domain team assembly with gender balance enforcement (≥40% M/F)
affects: [21-decision-memory, 22-rapportage-redesign]

tech-stack:
  added: []
  patterns: [functional-agent-team-selection, preset-as-pool-hint]

key-files:
  created: []
  modified: [deliberators/engine.py, deliberators/models.py, deliberators/loader.py, deliberators/__main__.py, config.yaml, CLAUDE.md, .claude/commands/deliberate.md, tests/test_engine.py, tests/test_config.py, tests/test_loader.py, tests/test_cli.py, tests/test_quality.py]
  deleted: [.claude/commands/deliberate-code.md]

key-decisions:
  - "Presets with fixed analysts/editors bypass team selection (backward compat for tests)"
  - "Team selection is a functional agent via _call_functional_agent(), same pattern as intake/convergence"
  - "Test config fixture _make_test_config() provides deterministic teams for existing engine tests"
  - "Intake always runs (code_* skip removed) — team selector handles code context awareness"

patterns-established:
  - "Functional agent pattern: intake → team selection → convergence — all use _call_functional_agent()"
  - "Preset as pool-hint: team_size/editor_count define team shape, not composition"

duration: ~30min
started: 2026-03-22T00:00:00Z
completed: 2026-03-22T23:59:00Z
---

# Phase 20 Plan 01: Dynamic Team Selection Summary

**TeamSelectionAgent assembles optimal teams from 54-persona pool; unified /deliberate command replaces both commands; presets define team shape not composition**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~30min |
| Started | 2026-03-22 |
| Completed | 2026-03-22 |
| Tasks | 2 completed |
| Files modified | 12 |
| Files deleted | 1 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: TeamSelectionAgent selects from pool | Pass | _run_team_selection() with catalog, parsing, validation, fallback |
| AC-2: Gender balance in selection prompt | Pass | System prompt includes "at least 40% representation of each binary gender" |
| AC-3: Preset uses team_size + editor_count | Pass | 3 presets in config.yaml, Preset dataclass updated, loader validates |
| AC-4: code_* presets removed, --files works | Pass | CLI accepts only quick/balanced/deep, --files works with any |
| AC-5: /deliberate-code removed | Pass | deliberate-code.md deleted, deliberate.md supports --files |
| AC-6: Intake runs for all questions | Pass | code_* skip logic removed, test_intake_always_runs verifies |
| AC-7: All tests pass | Pass | 1154 passed, 0 failed, 54 skipped |

## Accomplishments

- TeamSelectionAgent as 3rd functional agent (intake → team selection → convergence pipeline)
- Unified /deliberate command handles both general deliberation and code review
- Presets define team shape (team_size/editor_count), not fixed composition
- 9 new tests for team selection (4 parser unit tests + 5 integration tests)
- Clean removal of code_* presets with no regressions

## Task Commits

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| Task 1 + Task 2 | pending | feat | Team selection agent + unified command |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `deliberators/models.py` | Modified | team_size, editor_count on Preset; team_selected event |
| `deliberators/engine.py` | Modified | _run_team_selection(), _parse_team_selection_output(), _build_persona_catalog(); intake always runs |
| `deliberators/loader.py` | Modified | team_size/editor_count validation; removed validate_preset_personas() |
| `deliberators/__main__.py` | Modified | 3 presets only; team_selected event handler; removed validate call |
| `config.yaml` | Modified | 3 presets with team_size/editor_count, no fixed lists |
| `deliberators/data/config.yaml` | Modified | Synced bundled copy |
| `CLAUDE.md` | Modified | Updated documentation for unified command |
| `.claude/commands/deliberate.md` | Modified | Added --files support, updated preset docs |
| `.claude/commands/deliberate-code.md` | Deleted | Merged into deliberate.md |
| `tests/test_engine.py` | Modified | _make_test_config(), TestParseTeamSelectionOutput, TestTeamSelection |
| `tests/test_config.py` | Modified | 3 presets, team_size/editor_count tests |
| `tests/test_loader.py` | Modified | Updated config loader tests, removed validate_preset_personas |
| `tests/test_cli.py` | Modified | Removed code_* preset tests |
| `tests/test_quality.py` | Modified | Uses _make_test_config() fixture |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Fixed lists bypass team selection | Existing tests need deterministic teams; also useful for power users | Clean separation: dynamic default, override possible |
| Test config fixture pattern | Real config.yaml has no fixed lists, but engine tests need predictable team composition | _make_test_config() used by test_engine.py and test_quality.py |
| Team selection output parsing with role validation | LLM might suggest editors as analysts or vice versa | _parse_team_selection_output validates role matches |
| Fallback chain: preset fixed → pool default | Graceful degradation if LLM parsing fails | Never crashes, always runs a team |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | test_quality.py also needed config fixture update |
| Scope additions | 0 | — |
| Deferred | 0 | — |

**Total impact:** One auto-fix (test_quality.py config fixture), no scope creep

### Auto-fixed Issues

**1. test_quality.py config fixture**
- **Found during:** Task 1 verification (full test suite)
- **Issue:** test_quality.py used real ConfigLoader.load() which now returns presets without fixed lists, causing team selection failures in mocked tests
- **Fix:** Updated to use _make_test_config() from test_engine.py
- **Verification:** 1154 tests pass

## Next Phase Readiness

**Ready:**
- Phase 21 (Decision Memory) can build on the unified command
- Phase 22 (Rapportage Redesign) has team selection data available in events

**Concerns:**
- Bundled data sync remains manual (cp config.yaml deliberators/data/config.yaml)
- Slash command deliberate.md is large and has some stale sections referencing old preset format

**Blockers:**
- None

---
*Phase: 20-dynamic-team-selection, Plan: 01*
*Completed: 2026-03-22*
