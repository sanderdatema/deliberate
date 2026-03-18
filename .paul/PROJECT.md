# Deliberators

## What This Is

Een Claude Code skill die een team van AI-agents met verschillende denkstijlen orkestreert om in rondes te debatteren over een vraagstuk. Geinspireerd op Martijn Aslanders "Magische Dertien" — een ensemble van historische en fictieve denkers die elk een specifieke denkstijl afdwingen met harde constraints.

## Core Value

Gebruikers krijgen diepere, meer genuanceerde antwoorden op complexe vragen door multi-perspectief AI-debat.

## Current State

| Attribute | Value |
|-----------|-------|
| Version | 0.0.0 |
| Status | Prototype |
| Last Updated | 2026-03-18 |

## Requirements

### Validated (Shipped)

(none yet)

### Active (In Progress)

- [ ] Persona-definitie format (YAML met harde constraints per denker)
- [ ] Core orchestrator (spawnt agents, verzamelt output)
- [ ] Multi-ronde debat engine
- [ ] Fuzzy logic scoring (gewogen standpunten 0.0-1.0)
- [ ] Eindredactie/synthese fase
- [ ] Claude Code slash command integratie

### Out of Scope

- Web UI — CLI-first, slash command
- Persistente conversatie-geschiedenis — elke sessie is zelfstandig
- Fine-tuning of custom models — standaard Claude via Agent tool
- Exacte kopie van alle 13 Aslander-personages — configureerbaar team

## Target Users

**Primary:** Sander (en andere Claude Code gebruikers)
- Wil complexe vraagstukken vanuit meerdere perspectieven analyseren
- Gebruikt Claude Code dagelijks
- Waardeert vraagverschuiving (betere vragen, niet alleen betere antwoorden)

## Context

**Inspiratie:**
Martijn Aslanders artikel over zijn "Magische Dertien" — een team van virtuele denkers gebaseerd op Scott Pages Diversity Prediction Theorem. Kernidee: collectieve fout = gemiddelde individuele fout minus diversiteit van voorspellingen.

**Technische Context:**
- Claude Code Agent tool voor parallel agent spawning
- YAML persona-definities met harde constraints (niet stijlsuggesties)
- Fuzzy logic output (gewogen signalen i.p.v. binair waar/onwaar)
- Model routing: goedkopere modellen voor analyse, duurdere voor synthese

## Constraints

### Technical Constraints
- Moet werken als Claude Code slash command
- Agents communiceren via Claude Code Agent tool
- Persona's configureerbaar via YAML

### Business Constraints
- Kostenefficient: model routing per rol (Haiku/Sonnet voor analisten, Opus voor synthese)

## Key Decisions

| Decision | Rationale | Date | Status |
|----------|-----------|------|--------|
| Claude Code skill i.p.v. standalone CLI | Directe integratie in bestaande workflow | 2026-03-18 | Active |
| YAML persona-definities | Configureerbaar, leesbaar, uitbreidbaar | 2026-03-18 | Active |
| Fuzzy logic scoring | Aslanders gewogen signalen benadering | 2026-03-18 | Active |

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Runtime | Claude Code Agent tool | Parallel agent spawning |
| Persona's | YAML | Configureerbare denkstijlen |
| Orchestratie | Claude Code slash command | Entrypoint voor gebruiker |
| Scoring | Fuzzy logic (0.0-1.0) | Gewogen standpunten |

## Plane

- **Workspace:** sander-vibe
- **Project ID:** 4d8cbe02-7ecd-464f-887a-43edfee98da8
- **Prefix:** DELIB
- **Linked items:** None yet

---
*Created: 2026-03-18*
