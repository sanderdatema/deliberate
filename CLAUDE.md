# Deliberators

Multi-perspectief AI deliberatie team als Claude Code skill.

## Quick Start

```bash
# Run tests
uv run pytest

# General deliberation (balanced preset, default)
/deliberate "Your question here"

# Quick analysis (3 analysts + 1 editor, 1 round)
/deliberate --preset quick "Your question here"

# Deep analysis (8 analysts + 3 editors, max 3 rounds)
/deliberate --preset deep "Your question here"

# Code review (team selector picks code personas automatically)
/deliberate --files src/main.py src/utils.py "Review this module"

# Quick code review
/deliberate --preset quick --files src/main.py "Security check"

# Manage personal preferences (tone, style)
/deliberate-setting                    # List preferences
/deliberate-setting Niet paternalistisch  # Add preference
/deliberate-setting --remove 1         # Remove preference
```

## Presets

Teams are assembled dynamically by the team selection agent. Presets control team size and rounds.

| Preset | Team Size | Editors | Rounds | ~Time |
|--------|-----------|---------|--------|-------|
| quick | 3 analysts | 1 editor | 1 | ~3 min |
| balanced | 5 analysts | 2 editors | 2 | ~5 min |
| deep | 8 analysts | 3 editors | max 3 | ~8 min |

All presets include De Samenvatter as final editor for concrete, actionable output. When `--files` is provided, the team selector prioritizes code-focused personas.

## Persona Pool

25 active personas (20 analysts, 5 editors) + 29 archived across code, product, creative, and systems domains. The team selection agent picks the optimal subset for each question based on domain expertise and gender balance (≥40% M/F). Archived personas are in `personas/archived/` for re-activation.

## Custom Personas

Add a YAML file to `personas/` following the schema. It will be auto-discovered and available for team selection.

Required fields: `name`, `model`, `domains`, `role` (analyst/editor), `reasoning_style`, `forbidden` (list, min 2), `focus`, `output_format`, `system_prompt` (must contain FORBIDDEN/MUST NOT + FORMAT YOUR RESPONSE section).

## Directory Structure

```
config.yaml             # Presets and defaults
personas/               # 25 active persona definitions (YAML)
  archived/             # 29 archived personas
  schema.yaml           # Validation schema
  socrates.yaml         # Analysts (20 total)
  ...
  marx.yaml             # Editors (5 total)
  hegel.yaml
  arendt.yaml
  samenvatter.yaml
  code-synthesizer.yaml
deliberators/           # Python engine
  engine.py             # Async orchestration + team selection + synthesis
  storage.py            # Decision memory (JSON save/load/list)
  context.py            # CodeContextBuilder (file reading)
  loader.py             # YAML persona/config loaders
  models.py             # Data models (Persona, Config, DecisionRecord, etc.)
  prompts.py            # Pure prompt builders (analyst, editor, catalog)
  formatter.py          # Thematic report formatter (with per-persona appendix)
  web_pusher.py         # HTTP push client for web viewer
  web/                  # FastAPI WebSocket viewer package
    server.py           # FastAPI routes and WebSocket streaming
  __main__.py           # CLI entry point
tests/                  # Pytest validation suite
  test_personas.py      # Persona format validation
  test_config.py        # Config and preset validation
  test_loader.py        # Loader unit tests
  test_engine.py        # Engine orchestration tests
  test_prompts.py       # Prompt builder tests
  test_context.py       # CodeContextBuilder tests
  test_cli.py           # CLI parser and formatter tests
  test_storage.py       # Decision memory storage tests
  test_quality.py       # Behavioral/quality tests
  test_web.py           # Web viewer tests
.claude/commands/       # Claude Code slash commands
  deliberate.md         # Unified deliberation command (general + code review)
  deliberate-setting.md # User preference management
```

## User Preferences

Preferences are stored in `~/.local/share/deliberators/preferences.json` and injected as HIGH PRIORITY constraints into every analyst and editor prompt. Managed via `/deliberate-setting`.

## Architecture

### Deliberation (`/deliberate`)
1. Parses `--preset`, `--files` flags and loads `config.yaml`
2. **Intake:** Beoordeelt of de casus helder genoeg is, vraagt door
3. **Team Selection:** Selecteert optimaal team uit 25 persona pool (domains + genderbalans)
3b. **Team Approval:** Als `on_approve_team` callback is ingesteld, toont motivatie per persona en vraagt goedkeuring. Gebruiker kan team aanpassen.
4. Ronde 1: selected analysts spawn **in parallel**
5. Ronde 2+: analysts react to each other (adaptive, convergence check)
6. Editorial round: editors run **sequentially**
7. **De Samenvatter:** Concrete, alledaagse taal
8. **Synthesis:** Thematic report (landschap, spanningsvelden, blinde vlekken, verschuiving, actiepunten)
9. **Auto-save:** Decision record saved to `~/.local/share/deliberators/decisions/`

When `--files` is provided, code context is injected into analyst and editor prompts, and the team selector prioritizes code-focused personas.

When `--followup ID` is provided, the prior deliberation's conclusions are injected into analyst prompts as context.

## Testing

```bash
uv run pytest -v                      # All tests (736)
uv run pytest tests/test_personas.py  # Persona validation
uv run pytest tests/test_config.py    # Config/preset validation
uv run pytest tests/test_engine.py    # Engine orchestration
uv run pytest tests/test_context.py   # Code context builder
uv run pytest tests/test_storage.py   # Decision memory storage
```
