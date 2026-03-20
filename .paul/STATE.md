# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-03-20)

**Core value:** Gebruikers krijgen diepere, meer genuanceerde antwoorden op complexe vragen door multi-perspectief AI-debat
**Current focus:** v0.5 Global Install — COMPLETE

## Current Position

Milestone: v0.5 Global Install — COMPLETE
Phase: 15 of 15 (Slash Command Update) — Complete
Plan: 15-01 complete
Status: v0.5 milestone complete, package globally installable
Last activity: 2026-03-20 — Phase 15 UNIFY complete, milestone done

Progress:
- v0.1: [██████████] 100% ✓
- v0.2: [██████████] 100% ✓
- v0.3: [██████████] 100% ✓
- v0.4: [██████████] 100% ✓
- v0.5: [██████████] 100% ✓

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [Loop complete — milestone done]
```

## Accumulated Context

### Decisions (v0.1–v0.4)
- Opus voor alle agents
- Python engine met Anthropic API direct
- /deliberate-code als apart command
- Immutable tuple fields, path sanitization, autodiscovery

### Decisions (v0.5)
- hatchling as build backend (required by uv for scripts)
- Bundled data as subpackage deliberators/data/
- _BUNDLED_DATA_DIR constant (avoids circular import)
- Fallback chain: CWD → ~/.config/deliberators/ → bundled
- Slash commands resolve paths via uv run python -c

## Session Continuity

Last session: 2026-03-20
Stopped at: v0.5 milestone complete
Next action: /commit to commit all v0.5 changes
Resume file: .paul/phases/15-slash-command-update/15-01-SUMMARY.md

---
*STATE.md — Updated after every significant action*
