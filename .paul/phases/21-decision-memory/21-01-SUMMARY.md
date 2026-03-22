---
phase: 21-decision-memory
plan: 01
subsystem: engine, models, cli, storage
tags: [decision-memory, json-storage, history, followup]

requires:
  - phase: 20-dynamic-team-selection
    provides: unified /deliberate command, DeliberationResult with team data

provides:
  - DecisionRecord dataclass for structured deliberation storage
  - DecisionStore with save/load/list to ~/.local/share/deliberators/decisions/
  - CLI --history and --followup flags
  - Auto-save after every deliberation
affects: [22-rapportage-redesign]

tech-stack:
  added: []
  patterns: [decision-record-storage, followup-context-injection]

key-files:
  created: [deliberators/storage.py, tests/test_storage.py]
  modified: [deliberators/models.py, deliberators/engine.py, deliberators/__main__.py, CLAUDE.md]

key-decisions:
  - "Simple JSON files in ~/.local/share/deliberators/decisions/ — no database, no schema versioning"
  - "Short ID prefix matching for user convenience (abc1 matches abc12345)"
  - "question made optional (nargs='?') to support --history without question"
  - "Follow-up injects summary + key_positions only, not full analyst output (context budget)"

patterns-established:
  - "Decision record pattern: auto-save after deliberation, load by prefix ID"
  - "Prior context injection: PRIOR DELIBERATION CONTEXT block in analyst prompts"

duration: ~15min
started: 2026-03-22T00:00:00Z
completed: 2026-03-22T23:59:00Z
---

# Phase 21 Plan 01: Decision Memory Summary

**DecisionStore saves deliberation results as JSON; --history lists past decisions; --followup injects prior conclusions into new deliberations**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~15min |
| Started | 2026-03-22 |
| Completed | 2026-03-22 |
| Tasks | 2 completed |
| Files created | 2 |
| Files modified | 4 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: DecisionRecord model | Pass | Frozen dataclass with id, timestamp, question, preset_name, analysts, editors, summary, key_positions, follow_up_of |
| AC-2: Auto-save after deliberation | Pass | to_decision_record() + DecisionStore.save() in __main__.py after run() |
| AC-3: --history lists past deliberations | Pass | Prints table with date, short ID, preset, question (truncated) |
| AC-4: --followup injects prior context | Pass | PRIOR DELIBERATION CONTEXT block injected into _build_analyst_prompt |
| AC-5: All tests pass | Pass | 1161 passed, 0 failed, 54 skipped |

## Accomplishments

- DecisionRecord frozen dataclass with all required fields
- DecisionStore with save/load (full + prefix ID)/list_recent
- 7 new storage tests covering save, load, prefix match, list ordering, roundtrip
- CLI --history and --followup flags with proper error handling
- Auto-save after every deliberation with short ID feedback

## Task Commits

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| Task 1 + Task 2 | pending | feat | Decision memory storage + CLI integration |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `deliberators/models.py` | Modified | DecisionRecord frozen dataclass |
| `deliberators/storage.py` | Created | DecisionStore (save/load/list JSON files) |
| `deliberators/engine.py` | Modified | to_decision_record(), _condense_positions(), prior_decision param in run/prompts |
| `deliberators/__main__.py` | Modified | --history, --followup flags, auto-save, _print_history() |
| `tests/test_storage.py` | Created | 7 tests for storage operations |
| `CLAUDE.md` | Modified | Decision memory docs, storage.py in structure |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| JSON files in ~/.local/share/ | XDG-compliant, no dependencies, simple | Easy to inspect/backup, no migration needed |
| Prefix ID matching | UUIDs are long, users want short IDs | `store.load("abc1")` works if unique prefix |
| question nargs="?" | --history needs no question arg | Explicit error if question missing without --history |
| Key positions truncated to 200 chars | Full output would blow context budget on followup | Sufficient for context, not for reproduction |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 0 | — |
| Scope additions | 0 | — |
| Deferred | 0 | — |

**Total impact:** Plan executed exactly as written

## Next Phase Readiness

**Ready:**
- Phase 22 (Rapportage Redesign) can access stored decisions
- Decision records contain team composition data for reporting

**Concerns:**
- No cleanup/pruning of old decisions — could accumulate over time
- Slash command doesn't support --followup yet (CLI only)

**Blockers:**
- None

---
*Phase: 21-decision-memory, Plan: 01*
*Completed: 2026-03-22*
