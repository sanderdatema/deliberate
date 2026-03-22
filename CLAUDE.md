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

# Run via CLI (requires ANTHROPIC_API_KEY env var)
uv run python -m deliberators "Your question here" --preset balanced
uv run python -m deliberators "Review this code" --preset balanced --files src/main.py
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

54 personas (49 analysts, 5 editors) across 15+ expertise domains. The team selection agent picks the optimal subset for each question based on domain expertise and gender balance (≥40% M/F).

## Custom Personas

Add a YAML file to `personas/` following the schema. It will be auto-discovered and available for team selection.

Required fields: `name`, `model`, `domains`, `role` (analyst/editor), `reasoning_style`, `forbidden` (list, min 2), `focus`, `output_format`, `system_prompt` (must contain FORBIDDEN/MUST NOT + FORMAT YOUR RESPONSE section).

## Directory Structure

```
config.yaml             # Presets and defaults
personas/               # Thinker definitions (YAML, 54 personas)
  schema.yaml           # Validation schema
  socrates.yaml         # Analysts (49 total)
  ...
  marx.yaml             # Editors (5 total)
  hegel.yaml
  arendt.yaml
  samenvatter.yaml
  code-synthesizer.yaml
deliberators/           # Python engine
  engine.py             # Async orchestration + team selection
  context.py            # CodeContextBuilder (file reading)
  loader.py             # YAML persona/config loaders
  models.py             # Data models (Persona, Config, etc.)
  formatter.py          # Markdown output formatter
  web.py                # FastAPI WebSocket viewer
  __main__.py           # CLI entry point
tests/                  # Pytest validation suite
  test_personas.py      # Persona format validation
  test_config.py        # Config and preset validation
  test_loader.py        # Loader unit tests
  test_engine.py        # Engine orchestration tests
  test_context.py       # CodeContextBuilder tests
  test_cli.py           # CLI parser and formatter tests
  test_quality.py       # Behavioral/quality tests
  test_web.py           # Web viewer tests
.claude/commands/       # Claude Code slash commands
  deliberate.md         # Unified deliberation command (general + code review)
```

## Architecture

### Deliberation (`/deliberate`)
1. Parses `--preset`, `--files` flags and loads `config.yaml`
2. **Intake:** Beoordeelt of de casus helder genoeg is, vraagt door
3. **Team Selection:** Selecteert optimaal team uit 54 persona pool (domains + genderbalans)
4. Ronde 1: selected analysts spawn **in parallel**
5. Ronde 2+: analysts react to each other (adaptive, convergence check)
6. Editorial round: editors run **sequentially**
7. **De Samenvatter:** Concrete, alledaagse taal
8. Meta-analysis: consensus, dissensie, verschuiving

When `--files` is provided, code context is injected into analyst and editor prompts, and the team selector prioritizes code-focused personas.

## Testing

```bash
uv run pytest -v                      # All tests (1100+)
uv run pytest tests/test_personas.py  # Persona validation
uv run pytest tests/test_config.py    # Config/preset validation
uv run pytest tests/test_engine.py    # Engine orchestration
uv run pytest tests/test_context.py   # Code context builder
```
