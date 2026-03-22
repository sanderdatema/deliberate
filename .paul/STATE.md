# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-03-22)

**Core value:** Gebruikers krijgen diepere, meer genuanceerde antwoorden op complexe vragen door multi-perspectief AI-debat
**Current focus:** v0.6 Adaptive Deliberation — Phase 18 complete, ready for Phase 19

## Current Position

Milestone: v0.6 Adaptive Deliberation
Phase: 18 of 22 (Adaptive Rounds) — Complete
Plan: 18-01 complete
Status: Phase 18 done, ready for Phase 19 PLAN
Last activity: 2026-03-22 — Phase 18 APPLY+UNIFY complete; 622 tests pass

Progress:
- v0.1: [##########] 100%
- v0.2: [##########] 100%
- v0.3: [##########] 100%
- v0.4: [##########] 100%
- v0.5: [##########] 100%
- v0.6: [#####_____] 43%

## Loop Position

Current loop state:
```
PLAN --> APPLY --> UNIFY
  V        V        V     [Loop complete - Phase 18 done]
```

## Accumulated Context

### Decisions (v0.1-v0.5)
- Opus voor alle agents (v0.1-v0.5, gewijzigd in v0.6)
- Python engine met claude -p subprocessen (v0.5 wijziging)
- /deliberate-code als apart command (wordt gemerged in Phase 20)
- Immutable tuple fields, path sanitization, autodiscovery
- hatchling build backend, bundled data, fallback loader

### Decisions (v0.6)
- Per-persona model routing: Sonnet/Opus per YAML veld (Phase 16)
- Config.model blijft als fallback voor functionele agents (intake, convergentie)
- Lupin vervangen door Machiavelli (Phase 16, maar Lupin keert terug in Phase 19)
- Christensen vervangen door Knuth (Phase 16)
- Jony Ive herdefinieerd naar UI/UX design reviewer (Phase 16)
- Intake-agent en convergentie-agent worden functioneel (geen persona YAML)
- Intake skipped voor code_* presets (Phase 17, vervalt in Phase 20 met unified command)
- _call_functional_agent voor subprocess calls zonder Persona (Phase 17)
- Pool groeit, niemand gaat weg — intake selecteert dynamisch (Phase 19+20 besluit)
- /deliberate-code verdwijnt, één unified /deliberate command (Phase 20 besluit)
- Nieuwe personas: Joan Clarke, Margaret Hamilton, Barbara Liskov, Ada Lovelace, Hedy Lamarr, Alan Turing (Phase 19)

### Git State
Last commit: 6eecb11 (Phase 18 APPLY — adaptive rounds)
Branch: main
Feature branches merged: none

## Session Continuity

Last session: 2026-03-22
Stopped at: Phase 18 UNIFY complete
Next action: /paul:plan for Phase 19 (Pool Expansion — 29 new personas)
Resume file: .paul/phases/18-adaptive-rounds/18-01-SUMMARY.md

---
*STATE.md -- Updated after every significant action*
