# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-03-18)

**Core value:** Gebruikers krijgen diepere, meer genuanceerde antwoorden op complexe vragen door multi-perspectief AI-debat
**Current focus:** v0.2 — Python scripting engine + live web UI

## Current Position

Milestone: v0.2 Scripting Engine & Live UI
Phase: 4 of 6 (Python Orchestration Engine) — Planning
Milestone: Awaiting next milestone
Phase: None active
Plan: None
Status: v0.2 complete — ready for next
Last activity: 2026-03-18 — Milestone v0.2 completed

Progress:
- v0.1: [██████████] 100% ✓
- v0.2: [██████████] 100% ✓

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ○        ○        ○     [Milestone complete — ready for next]
```

## Accumulated Context

### Decisions (v0.1)
- Opus voor alle agents
- Multi-round: 2 rondes default (1 voor quick)
- 14 personas (10 analysts + 3 editors + samenvatter)
- 3 presets: quick/balanced/deep
- Custom persona auto-discovery

### Decisions (v0.2)
- Python engine met Anthropic API direct (niet Claude Code Agent tool)
- Event/callback systeem voor streaming
- Web UI via FastAPI + WebSocket
- Slash command wordt thin wrapper rond Python engine
- Bugfixes uit self-evaluation geïntegreerd in engine rewrite

### Self-Evaluation Findings (input for v0.2)
- Config/docs mismatch: quick preset 2 editors in config, 1 in docs → fix in 04-01
- Round 2 receives lossy summary instead of full output → fix in 04-02
- Zero runtime constraint validation → address in 04-02
- Custom persona auto-loading has weaker validation than test suite → fix in 04-01
- 159 format tests, zero quality/behavioral tests → add in 04-03
- Templar/Marx overlap in power analysis → address in Phase 6
- Deep preset ratio structurally unstable (10:3) → address in Phase 6

## Session Continuity

Last session: 2026-03-18
Stopped at: Milestone v0.2 complete
Next action: /paul:discuss-milestone or /paul:milestone
Resume file: .paul/MILESTONES.md

---
*STATE.md — Updated after every significant action*
