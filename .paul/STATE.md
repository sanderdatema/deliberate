# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-03-22)

**Core value:** Gebruikers krijgen diepere, meer genuanceerde antwoorden op complexe vragen door multi-perspectief AI-debat
**Current focus:** v0.6 Adaptive Deliberation — Phase 17 complete, Phase 18 next

## Current Position

Milestone: v0.6 Adaptive Deliberation
Phase: 17 of 20 (Intake Fase) — Complete
Plan: 17-01 unified
Status: Loop closed — ready for Phase 18
Last activity: 2026-03-22 — Phase 17 UNIFY complete, 607 tests pass

Progress:
- v0.1: [##########] 100%
- v0.2: [##########] 100%
- v0.3: [##########] 100%
- v0.4: [##########] 100%
- v0.5: [##########] 100%
- v0.6: [########__] 40%

## Loop Position

Current loop state:
```
PLAN --> APPLY --> UNIFY
  V        V        V     [Phase 17 complete]
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
- _call_functional_agent patroon herbruikbaar voor ConvergenceAgent (Phase 18)

### Git State
Last commit: 9a7dd73 (Phase 17 feat commit)
Branch: main
Feature branches merged: none

## Session Continuity

Last session: 2026-03-22
Stopped at: Phase 17 UNIFY complete
Next action: /paul:plan Phase 18 (Adaptive Rounds — ConvergenceAgent)
Resume file: .paul/phases/18-adaptive-rounds/ (to be created)

---
*STATE.md -- Updated after every significant action*
