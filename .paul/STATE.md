# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-03-22)

**Core value:** Gebruikers krijgen diepere, meer genuanceerde antwoorden op complexe vragen door multi-perspectief AI-debat
**Current focus:** v0.6 Adaptive Deliberation — Phase 18 planning complete

## Current Position

Milestone: v0.6 Adaptive Deliberation
Phase: 18 of 22 (Adaptive Rounds) — Planning
Plan: 18-01 created, awaiting approval
Status: PLAN created, ready for APPLY
Last activity: 2026-03-22 — Phase 18 PLAN created, roadmap expanded (5→7 phases)

Progress:
- v0.1: [##########] 100%
- v0.2: [##########] 100%
- v0.3: [##########] 100%
- v0.4: [##########] 100%
- v0.5: [##########] 100%
- v0.6: [####______] 29%

## Loop Position

Current loop state:
```
PLAN --> APPLY --> UNIFY
  V        O        O     [Plan created, awaiting approval]
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
Last commit: ac0e39a (Phase 17 UNIFY)
Branch: main
Feature branches merged: none

## Session Continuity

Last session: 2026-03-22
Stopped at: Phase 18 PLAN created
Next action: Review plan, then /paul:apply
Resume file: .paul/phases/18-adaptive-rounds/18-01-PLAN.md

---
*STATE.md -- Updated after every significant action*
