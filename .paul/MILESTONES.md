# Milestones

Completed milestone log for this project.

| Milestone | Completed | Duration | Stats |
|-----------|-----------|----------|-------|
| v0.1 Initial Release | 2026-03-18 | ~1 hour | 3 phases, 3 plans |
| v0.2 Scripting & Live UI | 2026-03-18 | ~2 hours | 3 phases, 5 plans |

---

## v0.1 Initial Release

**Completed:** 2026-03-18
**Duration:** ~1 hour

### Stats

| Metric | Value |
|--------|-------|
| Phases | 3 |
| Plans | 3 |
| Tests | 159 |

### Key Accomplishments

- 14 persona YAML files with hard constraints and schema validation
- Multi-round deliberation orchestration via Claude Code slash command
- 3 presets (quick/balanced/deep) with configurable analyst/editor composition
- Intake doorvraag-fase preventing garbage-in-garbage-out
- De Samenvatter as final concrete translator
- 159 format/schema tests

---

## v0.2 Scripting Engine & Live UI

**Completed:** 2026-03-18
**Duration:** ~2 hours

### Stats

| Metric | Value |
|--------|-------|
| Phases | 3 |
| Plans | 5 |
| Files changed | 20+ |
| Tests | 322 (was 159) |

### Key Accomplishments

- Python `deliberators/` package with frozen dataclasses and validated YAML loaders
- Async orchestration engine using Anthropic API with parallel analyst rounds (asyncio.gather)
- Event/callback system (on_event + on_text) enabling real-time streaming
- Bug fix: Round 2 now receives full R1 output instead of lossy compressed summary
- CLI entry point: `uv run python -m deliberators "question" --preset quick`
- Live web viewer (FastAPI + WebSocket) — display-only server, Claude Code pushes events
- `/deliberate --web` flag for live browser viewing during deliberation
- Ibn Khaldun persona (non-Western, cyclical historiography)
- Templar/Marx overlap resolved (Templar → moral psychology, Marx → structural power)
- Deep preset rebalanced: 8 analysts + 4 editors (was 10:4)
- 163 new tests (quality, engine, CLI, web, loader, model tests)

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| Frozen dataclasses over Pydantic | Simplicity, no extra dependency |
| messages.stream() for all API calls | Streaming-first enables web UI without refactoring |
| Web server is display-only viewer | Claude Code is the runner (user's subscription), no API key needed |
| User starts server in separate terminal | Prevents Claude Code from blocking its own process |
| asyncio.gather for parallel analysts | True parallel execution, sequential for editors |

---
