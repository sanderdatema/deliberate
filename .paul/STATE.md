# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-03-22)

**Core value:** Gebruikers krijgen diepere, meer genuanceerde antwoorden op complexe vragen door multi-perspectief AI-debat
**Current focus:** v0.6 Adaptive Deliberation — Phase 21 complete, ready for Phase 22

## Current Position

Milestone: v0.6 Adaptive Deliberation
Phase: 21 of 22 (Decision Memory) — Complete
Plan: 21-01 completed
Status: UNIFY phase complete — loop closed
Last activity: 2026-03-22 — Phase 21 complete

Progress:
- v0.1: [##########] 100%
- v0.2: [##########] 100%
- v0.3: [##########] 100%
- v0.4: [##########] 100%
- v0.5: [##########] 100%
- v0.6: [########__] 86%

## Loop Position

Current loop state:
```
PLAN --> APPLY --> UNIFY
  V        V        V     [Plan 21-01 complete, loop closed]
```

## Accumulated Context

### Decisions (v0.1-v0.5)
- Opus voor alle agents (v0.1-v0.5, gewijzigd in v0.6)
- Python engine met claude -p subprocessen (v0.5 wijziging)
- /deliberate-code als apart command (gemerged in Phase 20)
- Immutable tuple fields, path sanitization, autodiscovery
- hatchling build backend, bundled data, fallback loader

### Decisions (v0.6)
- Per-persona model routing: Sonnet/Opus per YAML veld (Phase 16)
- Config.model blijft als fallback voor functionele agents (intake, convergentie)
- Lupin vervangen door Machiavelli (Phase 16, maar Lupin keert terug in Phase 19)
- Christensen vervangen door Knuth (Phase 16)
- Jony Ive herdefinieerd naar UI/UX design reviewer (Phase 16)
- Intake-agent en convergentie-agent worden functioneel (geen persona YAML)
- Intake skipped voor code_* presets (Phase 17, vervallen in Phase 20 — unified command)
- _call_functional_agent voor subprocess calls zonder Persona (Phase 17)
- Pool groeit, niemand gaat weg — intake selecteert dynamisch (Phase 19+20 besluit)
- /deliberate-code verdwenen, één unified /deliberate command (Phase 20)
- 29 nieuwe personas: pool 25→54, 23F/28M/3N, domains veld op alle personas (Phase 19)
- TeamSelectionAgent als 3e functionele agent: intake → team selection → convergence (Phase 20)
- Presets definiëren team shape (team_size/editor_count), niet compositie (Phase 20)
- Gender balance enforcement: ≥40% M/F in selectieprompt (Phase 20)
- Fixed analyst/editor lists bypassen team selection (backward compat) (Phase 20)
- Decision memory: JSON files in ~/.local/share/deliberators/decisions/ (Phase 21)
- Follow-up injects summary + key_positions, niet volledige output (Phase 21)
- Prefix ID matching voor gebruiksgemak (Phase 21)

### Git State
Last commit: pending (Phase 21 complete)
Branch: main
Feature branches merged: none

## Session Continuity

Last session: 2026-03-22
Stopped at: Phase 21 complete, loop closed
Next action: /paul:plan for Phase 22 (Rapportage Redesign)
Resume file: .paul/ROADMAP.md

---
*STATE.md -- Updated after every significant action*
