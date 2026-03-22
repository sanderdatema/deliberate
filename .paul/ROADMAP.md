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
**Plans:**
- [x] 04-01: Package structure, data models, YAML loaders (2026-03-18)
- [x] 04-02: Async orchestration engine with Anthropic API (2026-03-18)
- [x] 04-03: CLI entry point, formatter, quality tests (2026-03-18)

### Phase 5: Live Web UI ✓
**Plans:**
- [x] 05-01: WebSocket server + HTML/JS frontend (2026-03-18)

### Phase 6: Integration & Polish ✓
**Plans:**
- [x] 06-01: Integration + persona polish + quality metrics (2026-03-18)

### v0.3 Deliberators for Code
Status: **Complete**
Phases: 3 of 3 complete

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 7 | Code Personas | 1 | Complete | 2026-03-18 |
| 8 | Code Context Pipeline | 1 | Complete | 2026-03-18 |
| 9 | Code Integration & Command | 1 | Complete | 2026-03-18 |

## Phase Details (v0.3)

### Phase 7: Code Personas ✓
- [x] 07-01: 9 code analyst personas + 1 code editor + 3 code presets (2026-03-18)

### Phase 8: Code Context Pipeline ✓
- [x] 08-01: CodeContextBuilder + engine prompt injection + CLI --files flag (2026-03-18)

### Phase 9: Code Integration & Command ✓
- [x] 09-01: /deliberate-code command + documentation + CLI tests (2026-03-18)

### v0.4 Reliability & Code Quality
Status: **Complete**
Phases: 3 of 3 complete

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 10 | Reliability Fixes (HIGH) | 1 | Complete | 2026-03-18 |
| 11 | Structure & Maintainability (MEDIUM) | 1 | Complete | 2026-03-19 |
| 12 | Defensive Hardening (LOW) | 1 | Complete | 2026-03-19 |

## Phase Details (v0.4)

### Phase 10: Reliability Fixes ✓
- [x] 10-01: WebPusher reuse + preset validatie + agent error handling (2026-03-18)

### Phase 11: Structure & Maintainability ✓
- [x] 11-01: Preset.summarizer + dead code + WebPusher extraction + autodiscovery (2026-03-19)

### Phase 12: Defensive Hardening ✓
- [x] 12-01: Path sanitization + filesize limit + tuple fields + class→function refactor (2026-03-19)

## Current Milestone

### v0.5 Global Install
Status: **Complete**
Phases: 3 of 3 complete

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 13 | Package Data Bundling | 1 | Complete | 2026-03-20 |
| 14 | Fallback Loader | 1 | Complete | 2026-03-20 |
| 15 | Slash Command Update | 1 | Complete | 2026-03-20 |

## Phase Details (v0.5)

### Phase 13: Package Data Bundling ✓
- [x] 13-01: Bundled data directory + hatchling build system + get_data_path() helper (2026-03-20)

### Phase 14: Fallback Loader ✓
- [x] 14-01: resolve_config_path() + resolve_personas_dir() + CLI integration (2026-03-20)

### Phase 15: Slash Command Update ✓
- [x] 15-01: Path resolution preamble + parameterized paths + global copies (2026-03-20)

### v0.6 Adaptive Deliberation
Status: **In progress**
Phases: 2 of 7 complete

Upgrade van one-shot deliberatie naar adaptief denksysteem: per-persona model routing, intake fase, adaptive rounds, genderdiversiteit, dynamische teamselectie, decision memory, en thematische rapportage.

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 16 | Persona & Model Routing | 1 | ✅ Complete | 2026-03-22 |
| 17 | Intake Fase | 1 | ✅ Complete | 2026-03-22 |
| 18 | Adaptive Rounds | 1 | Planning | |
| 19 | Pool Expansion | 1 | Not started | |
| 20 | Dynamic Team Selection | 1 | Not started | |
| 21 | Decision Memory | 1 | Not started | |
| 22 | Rapportage Redesign | 1 | Not started | |

## Phase Details (v0.6)

### Phase 16: Persona & Model Routing ✅
- [x] 16-01: Schema + models + loader + engine + persona swaps + model assignments (2026-03-22)

### Phase 17: Intake Fase ✅
- [x] 17-01: IntakeBrief + _run_intake() + _call_functional_agent() + clarification callback + CLI integration (2026-03-22)

### Phase 18: Adaptive Rounds
**Focus:** Convergentie-detectie vervangt vast aantal rondes. Functionele convergentie-agent evalueert na elke ronde of doorgaan waarde toevoegt. Preset `rounds` → `max_rounds` + `min_rounds`.

**Depends on:** Phase 17 (intake-brief gaat mee in convergence context)

### Phase 19: Pool Expansion
**Focus:** Persona pool uitbreiden naar breed expertpanel — niet beperkt tot "code" of "general" categorieën. Experts uit alle domeinen: technologie, politiek, wetenschap, kunst, communicatie, duurzaamheid, etc. Genderdiversiteit als harde eis. Persona YAML's krijgen `domains` veld voor expertise-matching. `role: analyst | editor` categorisering wordt heroverwogen. Niemand gaat weg — de pool groeit.

**Nieuwe personas (minimaal):** Joan Clarke (cryptanalyse), Margaret Hamilton (systems reliability), Barbara Liskov (abstractions), Ada Lovelace (algoritmisch denken), Hedy Lamarr (inventief denken), Alan Turing (formal correctness), Lupin (terug als contrarian). Plus verdere expansie: denk aan Greta Thunberg (duurzaamheid/activisme), Thorbecke (governance/staatsrecht), Shakespeare (taal/storytelling), Ian McKellen (presentatie/communicatie), en meer.

**Persona's moeten scherp omschreven zijn** — elk unieke expertise, duidelijke denkstijl, zodat intake agent effectief kan selecteren.

**Depends on:** Phase 16 (model routing — nieuwe personas krijgen model field)

### Phase 20: Dynamic Team Selection
**Focus:** Intake agent wordt teamsamensteller — analyseert vraag en selecteert optimaal team uit volledige pool. `/deliberate-code` verdwijnt, één unified `/deliberate` command. Presets worden pool-hints i.p.v. vaste lijsten. Cross-domein teams mogelijk (Thunberg + Jobs bij duurzame productvisie, Clarke + Schneier bij security, Shakespeare + McKellen bij communicatie-strategie). Intake agent matcht op `domains` veld + vraaganalyse.

**Genderbalans als selectiecriterium:** Intake agent moet bij teamselectie actief letten op genderbalans — niet alleen de pool is divers, elk samengesteld team moet dat ook zijn.

**Depends on:** Phase 19 (grotere, domein-getagde pool), Phase 17 (intake-agent)

### Phase 21: Decision Memory
**Focus:** Structured JSON opslag van deliberaties. CLI flags voor history en follow-up.

**Depends on:** Phase 16 (model routing)

### Phase 22: Rapportage Redesign
**Focus:** Thematische rapportage i.p.v. per-persona output. Geintegreerd document met landschap, spanningsveld, blinde vlekken, actiepunten.

**Depends on:** Phase 18 (convergentie-info), Phase 21 (actiepunten-structuur)

---
*Roadmap created: 2026-03-18*
*Last updated: 2026-03-22 after Phase 18 planning + roadmap expansion*
