---
phase: 04-python-engine
plan: 02
subsystem: engine
tags: [python, asyncio, anthropic-sdk, streaming, orchestration]

requires:
  - phase: 04-python-engine/01
    provides: Persona, Config, Preset, DeliberationEvent dataclasses, PersonaLoader, ConfigLoader
provides:
  - Async DeliberationEngine with parallel analyst rounds and sequential editors
  - DeliberationResult dataclass
  - Event callback system (on_event, on_text)
  - Streaming support via messages.stream()
  - Bug fix: Round 2 full output (not lossy summary)
affects: [04-03-cli-tests, 05-web-ui]

tech-stack:
  added: [pytest-asyncio]
  patterns: [asyncio.gather for parallel agents, async context manager streaming, _maybe_await for sync/async callback compat]

key-files:
  created:
    - deliberators/engine.py
    - tests/test_engine.py
  modified:
    - deliberators/__init__.py
    - pyproject.toml

key-decisions:
  - "Streaming via messages.stream() — enables future web UI without refactoring"
  - "on_event + on_text dual callbacks — events for structure, text for real-time streaming"
  - "_maybe_await pattern — supports both sync and async callbacks"
  - "Samenvatter output stored separately from editor_outputs — distinct role in result"

patterns-established:
  - "MockStream/MockTextStream test helpers for mocking Anthropic streaming API"
  - "make_mock_client() with response_map for persona-specific mock responses"
  - "asyncio.gather for parallel work, sequential await for accumulative work"

duration: 10min
started: 2026-03-18T14:40:00Z
completed: 2026-03-18T14:50:00Z
---

# Phase 4 Plan 02: Async Orchestration Engine Summary

**Async DeliberationEngine using Anthropic API with parallel analyst rounds, sequential editors, streaming, and event callbacks — plus Round 2 full-output bug fix**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~10 min |
| Tasks | 2 completed |
| Files created | 2 |
| Files modified | 2 |
| Tests | 293 collected, 279 passed, 14 skipped |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Full deliberation with mocked API | Pass | Quick=5 calls, balanced=14 calls |
| AC-2: Parallel analysts, sequential editors | Pass | asyncio.gather verified, editor accumulation verified |
| AC-3: Round 2 full output (not lossy) | Pass | Complete R1 text in R2 prompts, not summaries |
| AC-4: Events in correct order | Pass | Full event sequence verified |
| AC-5: Streaming text callback | Pass | on_text receives chunks from multiple agents |
| AC-6: Existing tests still pass | Pass | 279 passed, 14 skipped |

## Accomplishments

- Built `DeliberationEngine` that orchestrates full multi-round deliberation via Anthropic API
- Fixed self-evaluation bug: Round 2 now receives complete Round 1 output instead of lossy compressed summaries
- Event callback system ready for web UI streaming (Phase 5)
- 14 new engine tests with zero real API calls — fully offline mock suite

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `deliberators/engine.py` | Created | DeliberationEngine, DeliberationResult, MODEL_MAP, prompt builders |
| `tests/test_engine.py` | Created | 14 tests with MockStream/MockTextStream helpers |
| `deliberators/__init__.py` | Modified | Added DeliberationEngine, DeliberationResult exports |
| `pyproject.toml` | Modified | Added pytest-asyncio to dev deps, asyncio_mode=auto |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| messages.stream() not messages.create() | Streaming enables real-time UI in Phase 5 | All API calls are streaming-first |
| Dual callbacks (on_event + on_text) | Events for structure, text for real-time | Clean separation for different consumers |
| _maybe_await helper | Support sync and async callbacks | Flexibility for simple and complex consumers |
| Samenvatter separate from editor_outputs | Different semantic role | Cleaner result structure |

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

**Ready:**
- Engine is complete and testable — Plan 04-03 can add CLI and quality tests
- Event system ready for Phase 5 (WebSocket streaming)
- DeliberationResult provides all data for formatting/display

**Concerns:**
- None

**Blockers:**
- None

---
*Phase: 04-python-engine, Plan: 02*
*Completed: 2026-03-18*
