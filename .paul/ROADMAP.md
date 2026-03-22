# Roadmap: Deliberators

## Overview

Van leeg project naar een werkende Claude Code skill die een configureerbaar team van AI-denkers orkestreert voor multi-perspectief debat over complexe vraagstukken. v0.2 breidt uit met een Python scripting engine en live web UI.

## Milestones

### v0.1 Initial Release
Status: **Complete**
Phases: 3 of 3 complete

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Foundation & Persona's | 1 | Complete | 2026-03-18 |
| 2 | Debat Engine & Fuzzy Logic | 1 | Complete | 2026-03-18 |
| 3 | Configuratie & Presets | 1 | Complete | 2026-03-18 |

### v0.2 Scripting Engine & Live UI
Status: **Complete**
Phases: 3 of 3 complete

Driven by self-evaluation findings: config/docs bugs, lossy R2 input, zero quality tests, plus user requests for programmatic access and real-time visualization.

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 4 | Python Orchestration Engine | 3 | Complete | 2026-03-18 |
| 5 | Live Web UI | 1 | Complete | 2026-03-18 |
| 6 | Integration & Polish | 1 | Complete | 2026-03-18 |

## Phase Details (v0.1)

### Phase 1: Foundation & Persona's
- [x] 01-01: Persona's, slash command, en validatie tests (2026-03-18)

### Phase 2: Debat Engine & Fuzzy Logic
- [x] 02-01: Multi-ronde debat + fuzzy scoring + consensus detectie (2026-03-18)

### Phase 3: Configuratie & Presets
- [x] 03-01: Configuratie, presets, en custom persona's (2026-03-18)

## Phase Details (v0.2)

### Phase 4: Python Orchestration Engine ✓
**Goal:** Extract orchestration from slash command prompt into a Python package using Anthropic API directly. This enables programmatic access, event streaming, and CLI usage outside Claude Code.

**Plans:**
- [x] 04-01: Package structure, data models, YAML loaders (2026-03-18)
- [x] 04-02: Async orchestration engine with Anthropic API (2026-03-18)
- [x] 04-03: CLI entry point, formatter, quality tests (2026-03-18)

**Key deliverables:**
- Python package `deliberators/` with async orchestration engine
- Persona/config loaders (YAML → dataclasses)
- Event/callback system (agent_started, agent_completed, round_started, etc.)
- CLI: `uv run python -m deliberators "question" --preset balanced`
- Fix bugs from self-evaluation (config/docs mismatch, lossy R2, validation gaps)
- Behavioral/quality tests alongside existing format tests

**Estimated plans:** 3 (package setup + persona/config, orchestration engine, CLI + bugfixes + tests)

### Phase 5: Live Web UI
**Goal:** Web interface that streams deliberation progress in real-time, showing agent panels, round transitions, confidence shifts, and position changes as they happen.

**Key deliverables:**
- WebSocket server (FastAPI) streaming events from orchestration engine
- HTML/JS frontend with agent panels showing live output
- Visual round progression timeline
- Confidence score visualization
- Full report + Samenvatter companion view

**Depends on:** Phase 4 (event system)
**Estimated plans:** 2 (backend + WebSocket, frontend)

### Phase 6: Integration & Polish
**Goal:** Wire everything together, update slash command, improve personas based on self-evaluation, add quality metrics.

**Key deliverables:**
- Slash command as thin wrapper calling Python engine
- Non-Western persona(s) for broader epistemic diversity
- Deep preset rebalancing (analyst/editor ratio)
- Samenvatter as companion alongside full report
- Templar/Marx overlap resolution
- Output quality benchmark (A/B vs single prompt)

**Depends on:** Phase 4, Phase 5
**Estimated plans:** 2 (integration + persona polish, benchmarking)

### v0.3 Deliberators for Code
Status: **Complete**
Phases: 3 of 3 complete

Multi-perspectief code review met developer/designer personas (Linus Torvalds, Kent Beck, Martin Fowler, Bruce Schneier, Steve Jobs, Don Norman, Jony Ive, Clayton Christensen, Grace Hopper). Agents kunnen code lezen en de gebruiker-fit beoordelen.

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 7 | Code Personas | 1 | Complete | 2026-03-18 |
| 8 | Code Context Pipeline | 1 | Complete | 2026-03-18 |
| 9 | Code Integration & Command | 1 | Complete | 2026-03-18 |

## Phase Details (v0.3)

### Phase 7: Code Personas ✓
**Focus:** Create 9 analyst + 1 editor YAML personas for code review, with code-specific forbidden constraints and output formats. Each persona modeled after a real developer/designer.

**Plans:**
- [x] 07-01: 9 code analyst personas + 1 code editor + 3 code presets (2026-03-18)

**Personas:** Linus Torvalds (code purist), Kent Beck (simplicity/TDD), Martin Fowler (architecture), Bruce Schneier (security), Steve Jobs (product vision), Don Norman (UX), Jony Ive (UI/UX design), Donald Knuth (algorithmic performance), Grace Hopper (pragmatism)

### Phase 8: Code Context Pipeline ✓
**Focus:** Pre-analysis step that reads codebase structure, key files, and patterns; feeds context to agents. Enable agents to use Read/Grep/Glob tools for code exploration during deliberation. Use Serena MCP for semantic code understanding.

**Plans:**
- [x] 08-01: CodeContextBuilder + engine prompt injection + CLI --files flag (2026-03-18)

**Depends on:** Phase 7 (personas exist)

### Phase 9: Code Integration & Command ✓
**Focus:** New `/deliberate-code` command (or `--mode code` flag), code-specific presets (quick/balanced/deep), intake adapted for user-fit questions ("Who are you? What do you want from this code?"), web viewer support.

**Plans:**
- [x] 09-01: /deliberate-code command + documentation + CLI tests (2026-03-18)

**Depends on:** Phase 7, Phase 8

### v0.4 Reliability & Code Quality
Status: **Complete**
Phases: 3 of 3 complete

Gedreven door de `/deliberate-code` self-review: 5 reviewers (Linus, Kent Beck, Fowler, Schneier, Hopper) identificeerden 10 actiepunten gerangschikt op severity.

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 10 | Reliability Fixes (HIGH) | 1 | Complete | 2026-03-18 |
| 11 | Structure & Maintainability (MEDIUM) | 1 | Complete | 2026-03-19 |
| 12 | Defensive Hardening (LOW) | 1 | Complete | 2026-03-19 |

## Phase Details (v0.4)

### Phase 10: Reliability Fixes ✓
**Focus:** Fix de 3 HIGH-priority bevindingen: WebPusher connection churn, silent persona failures, en ontbrekende error handling in _call_agent.

**Plans:**
- [x] 10-01: WebPusher reuse + preset validatie + agent error handling (2026-03-18)

**Key deliverables:**
- WebPusher hergebruikt één httpx.AsyncClient per sessie
- Preset-validatie controleert of persona-keys bestaan bij laden
- Warning logging bij ontbrekende personas in engine
- _call_agent vangt API-fouten per agent op (deliberatie gaat door)

### Phase 11: Structure & Maintainability ✓
**Focus:** MEDIUM-priority bevindingen: magic string "samenvatter", dead code in formatter, WebPusher extractie, STANDARD_PERSONAS autodiscovery.

**Plans:**
- [x] 11-01: Preset.summarizer + dead code + WebPusher extraction + autodiscovery (2026-03-19)

**Key deliverables:**
- Configurable summarizer via Preset.summarizer field in config.yaml
- WebPusher extracted to deliberators/web_pusher.py
- Persona autodiscovery via glob (no hardcoded STANDARD_PERSONAS)
- Dead code removed from formatter.py

### Phase 12: Defensive Hardening ✓
**Focus:** LOW-priority bevindingen: path-sanitisatie + filesize limiet in context.py, tuple ipv list in frozen dataclasses, CodeContextBuilder als module-functies.

**Plans:**
- [x] 12-01: Path sanitization + filesize limit + tuple fields + class→function refactor (2026-03-19)

**Key deliverables:**
- Path traversal rejection (`.." in path.parts`)
- Filesize limit (MAX_FILE_SIZE = 1 MB)
- Immutable tuple fields in Persona and Preset frozen dataclasses
- `build_code_context()` module function replaces CodeContextBuilder class

## Current Milestone

### v0.5 Global Install
Status: **Complete**
Phases: 3 of 3 complete

Maak `deliberators` installeerbaar via `uv tool install` zodat `/deliberate` en `/deliberate-code` vanuit elk project werken. Personas en config gebundeld als package data, loader zoekt eerst lokaal, dan in `~/.config/deliberators/`, dan in de package.

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 13 | Package Data Bundling | 1 | Complete | 2026-03-20 |
| 14 | Fallback Loader | 1 | Complete | 2026-03-20 |
| 15 | Slash Command Update | 1 | Complete | 2026-03-20 |

## Phase Details (v0.5)

### Phase 13: Package Data Bundling ✓
**Focus:** Move `personas/` en `config.yaml` inside het Python package als `package_data`. Voeg `[project.scripts]` entry point toe in `pyproject.toml`. Update version naar 0.5.0.

**Plans:**
- [x] 13-01: Bundled data directory + hatchling build system + get_data_path() helper (2026-03-20)

**Key deliverables:**
- `deliberators/data/` met gebundelde config.yaml en 26 persona YAML files
- `[build-system]` met hatchling backend
- `[project.scripts]` entry point: `deliberators` CLI command
- `get_data_path()` helper in `__init__.py`
- Version bump naar 0.5.0

### Phase 14: Fallback Loader ✓
**Focus:** Update `loader.py` met fallback-keten: CWD → `~/.config/deliberators/` → gebundelde package data. Update `__main__.py` arg defaults om de fallback-keten te gebruiken.

**Plans:**
- [x] 14-01: resolve_config_path() + resolve_personas_dir() + CLI integration (2026-03-20)

**Key deliverables:**
- `resolve_config_path()` en `resolve_personas_dir()` met 3-level fallback
- `__main__.py` gebruikt resolve functions
- CLI werkt vanuit elke directory

### Phase 15: Slash Command Update ✓
**Focus:** Update globale `~/.claude/commands/deliberate.md` en `deliberate-code.md` om de geïnstalleerde package te gebruiken. Verifieer dat `uv tool install .` werkt end-to-end.

**Plans:**
- [x] 15-01: Path resolution preamble + parameterized paths + global copies (2026-03-20)

**Key deliverables:**
- Step 0.5 "Resolve Data Paths" in beide commands
- CONFIG_PATH en PERSONAS_DIR geparametriseerd
- Global copies bijgewerkt in `~/.claude/commands/`

### v0.6 Adaptive Deliberation
Status: **In progress**
Phases: 1 of 5 complete

Upgrade van one-shot deliberatie naar adaptief denksysteem: per-persona model routing, intake fase, adaptive rounds met convergentie-detectie, decision memory, en thematische rapportage.

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 16 | Persona & Model Routing | 1 | ✅ Complete | 2026-03-22 |
| 17 | Intake Fase | 1 | Not started | |
| 18 | Adaptive Rounds | 1 | Not started | |
| 19 | Decision Memory | 1 | Not started | |
| 20 | Rapportage Redesign | 1 | Not started | |

## Phase Details (v0.6)

### Phase 16: Persona & Model Routing ✅
**Focus:** Persona-wijzigingen (Lupin→Machiavelli, Christensen→Knuth, Ive→UI/UX) en per-persona model routing (Sonnet/Opus per YAML). Fundering voor alle volgende phases.

**Plans:**
- [x] 16-01: Schema + models + loader + engine + persona swaps + model assignments (2026-03-22)

**Key deliverables:**
- `model: opus|sonnet` veld in alle persona YAML's
- Engine gebruikt per-persona model i.p.v. globaal config.model
- Machiavelli (strategisch realist) vervangt Lupin
- Knuth (performance/algorithmic) vervangt Christensen
- Ive herdefinieerd naar UI/UX design reviewer

### Phase 17: Intake Fase
**Focus:** Functionele intake-agent die vraag analyseert op helderheid, missende context, impliciete aannames. Produceert intake-brief die meegaat naar analysts.

**Depends on:** Phase 16 (model routing voor intake-agent)

### Phase 18: Adaptive Rounds
**Focus:** Convergentie-detectie vervangt vast aantal rondes. Functionele convergentie-agent evalueert na elke ronde of doorgaan waarde toevoegt.

**Depends on:** Phase 17 (intake-brief gaat mee in convergence context)

### Phase 19: Decision Memory
**Focus:** Structured JSON opslag van deliberaties. CLI flags voor history en follow-up.

**Depends on:** Phase 16 (model routing)

### Phase 20: Rapportage Redesign
**Focus:** Thematische rapportage i.p.v. per-persona output. Geintegreerd document met landschap, spanningsveld, blinde vlekken, actiepunten.

**Depends on:** Phase 18 (convergentie-info), Phase 19 (actiepunten-structuur)

---
*Roadmap created: 2026-03-18*
*Last updated: 2026-03-22*
