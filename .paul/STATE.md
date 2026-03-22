# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-03-22)

**Core value:** Gebruikers krijgen diepere, meer genuanceerde antwoorden op complexe vragen door multi-perspectief AI-debat
**Current focus:** v0.6 Adaptive Deliberation — Phase 17 complete

## Current Position

Milestone: v0.6 Adaptive Deliberation
Phase: 17 of 20 (Intake Fase) — Complete
Plan: 17-01 executed
Status: APPLY complete, ready for UNIFY
Last activity: 2026-03-22 — Phase 17 APPLY complete, 607 tests pass

Progress:
- v0.1: [##########] 100%
- v0.2: [##########] 100%
- v0.3: [##########] 100%
- v0.4: [##########] 100%
- v0.5: [##########] 100%
- v0.6: [####______] 20%

## Loop Position

Current loop state:
```
PLAN --> APPLY --> UNIFY
  V        V        O     [APPLY complete, ready for UNIFY]
```

## Accumulated Context

### Decisions (v0.1-v0.5)
- Opus voor alle agents (v0.1-v0.5, gewijzigd in v0.6)
- Python engine met claude -p subprocessen (v0.5 wijziging)
- /deliberate-code als apart command
- Immutable tuple fields, path sanitization, autodiscovery
- hatchling build backend, bundled data, fallback loader

### Decisions (v0.6)
- Per-persona model routing: Sonnet/Opus per YAML veld (Phase 16)
- Config.model blijft als fallback voor functionele agents (intake, convergentie)
- Lupin vervangen door Machiavelli (strategisch realist)
- Christensen vervangen door Knuth (performance analyst)
- Jony Ive herdefinieerd naar UI/UX design reviewer (wat gebruikers zien)
- Intake-agent en convergentie-agent worden functioneel (geen persona YAML)
- Intake skipped voor code_* presets (Phase 17)
- _call_functional_agent voor subprocess calls zonder Persona (Phase 17)

### Git State
Last commit: ee02131
Branch: main
Feature branches merged: none

## Session Continuity

Last session: 2026-03-22
Stopped at: Phase 17 APPLY complete
Next action: Commit, then /paul:unify to close loop, then Phase 18
Resume file: .paul/phases/17-intake-fase/17-01-PLAN.md

---
*STATE.md -- Updated after every significant action*
