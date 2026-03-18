# Roadmap: Deliberators

## Overview

Van leeg project naar een werkende Claude Code skill die een configureerbaar team van AI-denkers orkestreert voor multi-perspectief debat over complexe vraagstukken.

## Current Milestone

**v0.1 Initial Release** (v0.1.0)
Status: In progress
Phases: 2 of 3 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Foundation & Persona's | 1 | Complete | 2026-03-18 |
| 2 | Debat Engine & Fuzzy Logic | 1 | Complete | 2026-03-18 |
| 3 | Configuratie & Presets | 1 | Planning | - |

*Note: Original Phase 3 (Claude Code Integratie) was already completed as part of Phase 1+2. Original Phase 3+4 merged into new Phase 3.*

## Phase Details

### Phase 1: Foundation & Persona's

**Goal:** Werkende persona-definities in YAML en basis-orchestrator
**Depends on:** Nothing (first phase)

**Plans:**
- [x] 01-01: Persona's, slash command, en validatie tests (2026-03-18)

### Phase 2: Debat Engine & Fuzzy Logic

**Goal:** Multi-ronde debat waarbij agents op elkaars output reageren, met fuzzy scoring
**Depends on:** Phase 1

**Plans:**
- [x] 02-01: Multi-ronde debat + fuzzy scoring + consensus detectie (2026-03-18)

### Phase 3: Configuratie & Presets

**Goal:** Configureerbaar team, presets (quick/balanced/deep), en custom persona support
**Depends on:** Phase 2
**Research:** Unlikely (UX refinement)

**Scope:**
- Configuratie YAML (team selectie, aantal rondes, model routing)
- Preset teams: quick (3 analysts + 1 editor), balanced (5+3, default), deep (alle 13 Aslander-figuren)
- Custom persona support (user YAML in project)
- Output formatting verfijning

**Plans:**
- [ ] 03-01: Configuratie, presets, en custom persona's

---
*Roadmap created: 2026-03-18*
*Last updated: 2026-03-18*
