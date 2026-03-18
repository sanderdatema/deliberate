# Roadmap: Deliberators

## Overview

Van leeg project naar een werkende Claude Code skill die een configureerbaar team van AI-denkers orkestreert voor multi-perspectief debat over complexe vraagstukken.

## Current Milestone

**v0.1 Initial Release** (v0.1.0)
Status: In progress
Phases: 1 of 4 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Foundation & Persona's | 1 | Complete | 2026-03-18 |
| 2 | Debat Engine & Fuzzy Logic | 1 | Planning | - |
| 3 | Claude Code Integratie | TBD | Not started | - |
| 4 | Polish & Presets | TBD | Not started | - |

## Phase Details

### Phase 1: Foundation & Persona's

**Goal:** Werkende persona-definities in YAML en basis-orchestrator die een enkele agent kan spawnen
**Depends on:** Nothing (first phase)
**Research:** Unlikely (established patterns)

**Scope:**
- Project setup (package structure)
- YAML persona format met harde constraints
- Starter-set persona's (Socrates, Occam, Da Vinci, Holmes, Lupin, Marx, Hegel, Arendt)
- Basis orchestrator die persona's laadt en een agent spawnt

**Plans:**
- [x] 01-01: Persona's, slash command, en validatie tests (2026-03-18)

### Phase 2: Debat Engine & Fuzzy Logic

**Goal:** Multi-ronde debat waarbij agents op elkaars output reageren, met fuzzy scoring
**Depends on:** Phase 1 (persona's en orchestrator)
**Research:** Likely (prompt engineering voor gestructureerde output)
**Research topics:** Optimale prompt structuur voor fuzzy scoring output

**Scope:**
- Multi-ronde debat flow (parallel agent spawning per ronde)
- Fuzzy logic output format (confidence scores, evidence, challenges)
- Score aggregatie en consensus/polarisatie detectie
- Eindredactie fase (blinde vlekken, synthese)

**Plans:**
- [ ] 02-01: Multi-ronde debat + fuzzy scoring + consensus detectie

### Phase 3: Claude Code Integratie

**Goal:** Werkende slash command `/deliberate` die het volledige debat orkestreert
**Depends on:** Phase 2 (debat engine)
**Research:** Unlikely (Claude Code patterns known)

**Scope:**
- Slash command definitie
- Agent-based execution via Claude Code Agent tool
- Configuratie (team, rondes, model routing)
- Output formatting als markdown

**Plans:**
- [ ] 03-01: Slash command en Agent-based executor
- [ ] 03-02: Configuratie en model routing

### Phase 4: Polish & Presets

**Goal:** Gebruiksvriendelijke presets en gepolijste output
**Depends on:** Phase 3 (werkende integratie)
**Research:** Unlikely (UX refinement)

**Scope:**
- Preset teams (quick/balanced/deep)
- Progress indicators
- Output formatting en rapport structuur
- Custom persona support

**Plans:**
- [ ] 04-01: Presets en progress
- [ ] 04-02: Output formatting en custom persona's

---
*Roadmap created: 2026-03-18*
*Last updated: 2026-03-18*
