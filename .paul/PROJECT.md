# Deliberators

## What This Is

Een Claude Code skill die een team van AI-agents met verschillende denkstijlen orkestreert om in rondes te debatteren over een vraagstuk. Geinspireerd op Martijn Aslanders "Magische Dertien" — een ensemble van historische en fictieve denkers die elk een specifieke denkstijl afdwingen met harde constraints.

## Core Value

Gebruikers krijgen diepere, meer genuanceerde antwoorden op complexe vragen door multi-perspectief AI-debat.

## Current State

| Attribute | Value |
|-----------|-------|
| Version | 0.2.0 |
| Status | Feature-complete: slash command + scripting engine + web viewer |
| Last Updated | 2026-03-18 |

## Requirements

### Validated (Shipped — v0.1)

- [x] Persona-definitie format (YAML met harde constraints per denker)
- [x] Core orchestrator (spawnt agents, verzamelt output)
- [x] Multi-ronde debat engine
- [x] Fuzzy logic scoring (gewogen standpunten 0.0-1.0)
- [x] Eindredactie/synthese fase
- [x] Claude Code slash command integratie
- [x] 3 presets (quick/balanced/deep)
- [x] Intake doorvraag-fase
- [x] De Samenvatter concrete vertaler
- [x] 159 format/schema tests

### Validated (Shipped — v0.2)

- [x] Python scripting engine (Anthropic API direct, niet via Agent tool)
- [x] Event/callback systeem voor real-time voortgang
- [x] CLI entry point (`uv run python -m deliberators`)
- [x] Live Web UI (WebSocket streaming van agent output)
- [x] Bugfixes uit self-evaluation (config/docs mismatch, lossy R2 input, validatie gaps)
- [x] Behavioral/quality tests (niet alleen format)
- [x] Non-Western persona (Ibn Khaldun)
- [x] Templar/Marx overlap opgelost
- [x] Deep preset geherbalanceerd (8:4 ratio)

### Out of Scope

- Persistente conversatie-geschiedenis — elke sessie is zelfstandig
- Fine-tuning of custom models — standaard Claude via Anthropic API
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
- v0.1: Claude Code Agent tool voor parallel agent spawning (slash command)
- v0.2: Python scripting engine met Anthropic API voor programmatic access + web UI
- YAML persona-definities met harde constraints (niet stijlsuggesties)
- Fuzzy logic output (gewogen signalen i.p.v. binair waar/onwaar)
- Model routing: goedkopere modellen voor analyse, duurdere voor synthese

## Constraints

### Technical Constraints
- Slash command blijft werken (thin wrapper rond Python engine)
- Python engine gebruikt Anthropic API direct (asyncio + parallel calls)
- Persona's configureerbaar via YAML
- Web UI moet real-time agent output streamen

### Business Constraints
- Kostenefficient: model routing per rol (Haiku/Sonnet voor analisten, Opus voor synthese)

## Key Decisions

| Decision | Rationale | Date | Status |
|----------|-----------|------|--------|
| Claude Code skill i.p.v. standalone CLI | Directe integratie in bestaande workflow | 2026-03-18 | Active |
| YAML persona-definities | Configureerbaar, leesbaar, uitbreidbaar | 2026-03-18 | Active |
| Fuzzy logic scoring | Aslanders gewogen signalen benadering | 2026-03-18 | Active |
| Python engine + Anthropic API | Programmatic access, events, web UI mogelijk | 2026-03-18 | Active |
| Slash command als thin wrapper | Backward-compatible, engine doet het werk | 2026-03-18 | Active |

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Engine | Python + anthropic SDK | Async orchestratie, parallel API calls |
| Persona's | YAML + dataclasses | Configureerbare denkstijlen |
| Events | Callback/async generators | Real-time voortgang streaming |
| CLI | Click/Typer of bare argparse | `uv run python -m deliberators` |
| Web UI | FastAPI + WebSocket + HTML/JS | Live agent output visualisatie |
| Slash command | Claude Code command (thin wrapper) | Backward-compatible entrypoint |
| Scoring | Fuzzy logic (0.0-1.0) | Gewogen standpunten |

## Plane

- **Workspace:** sander-vibe
- **Project ID:** 4d8cbe02-7ecd-464f-887a-43edfee98da8
- **Prefix:** DELIB
- **Linked items:** None yet

---
*Created: 2026-03-18*
