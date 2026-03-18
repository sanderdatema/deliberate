# Deliberators

Multi-perspectief AI deliberatie team als Claude Code skill.

## Quick Start

```bash
# Run tests
uv run pytest

# Use the deliberation skill (balanced preset, default)
/deliberate "Your question here"

# Quick analysis (3 analysts + 2 editors, 1 round)
/deliberate --preset quick "Your question here"

# Deep analysis (10 analysts + 3 editors, 2 rounds)
/deliberate --preset deep "Your question here"

# Run via CLI (requires ANTHROPIC_API_KEY env var)
uv run python -m deliberators "Your question here" --preset quick
uv run python -m deliberators "Your question here" --preset balanced
uv run python -m deliberators "Your question here"  # uses default preset
```

## Presets

| Preset | Analysts | Editors | Rounds | ~Time |
|--------|----------|---------|--------|-------|
| quick | 3 (Occam, Holmes, Lupin) | 2 (Marx, Samenvatter) | 1 | ~3 min |
| balanced | 5 (Socrates, Occam, Da Vinci, Holmes, Lupin) | 3 (Marx, Hegel, Arendt) | 2 | ~5 min |
| deep | 8 (incl. Ibn Khaldun) | 3 (Marx, Hegel, Arendt) | 2 | ~8 min |

All presets include De Samenvatter as final editor for concrete, actionable output.

## Custom Personas

Add a YAML file to `personas/` following the schema. It will be auto-loaded alongside the preset.

Required fields: `name`, `role` (analyst/editor), `reasoning_style`, `forbidden` (list, min 2), `focus`, `output_format`, `system_prompt` (must contain FORBIDDEN/MUST NOT + FORMAT YOUR RESPONSE section).

## Directory Structure

```
config.yaml             # Presets and defaults
personas/               # Thinker definitions (YAML)
  schema.yaml           # Validation schema
  socrates.yaml         # Analysts — original 5
  occam.yaml
  da-vinci.yaml
  holmes.yaml
  lupin.yaml
  templar.yaml          # Analysts — extended
  tubman.yaml
  weil.yaml
  marple.yaml
  noether.yaml
  ibn-khaldun.yaml      # Analyst — non-Western (cyclical historiography)
  marx.yaml             # Editors (3)
  hegel.yaml
  arendt.yaml
  samenvatter.yaml      # Samenvatter — concrete vertaler (always last)
tests/                  # Pytest validation suite
  test_personas.py      # Persona format validation (159 tests)
  test_config.py        # Config and preset validation
.claude/commands/       # Claude Code slash commands
  deliberate.md         # Main orchestration command
```

## Architecture

1. `/deliberate` parses `--preset` flag and loads `config.yaml`
2. **Step 0 — Intake:** Beoordeelt of de casus helder genoeg is. Vraagt door via AskUserQuestion (max 12 vragen) tot de context compleet is. Pas daarna start de deliberatie.
3. Ronde 1: preset analysts spawn **in parallel** (all Opus)
4. Ronde 2: analysts react to each other's Round 1 output (skipped in quick)
5. Editorial round: editors run **sequentially** with accumulated context
6. **De Samenvatter:** Vertaalt het hele rapport naar concrete, alledaagse taal
7. Meta-analysis: consensus, dissensie, verschuiving, gewogen conclusie

## Testing

```bash
uv run pytest -v                      # All tests
uv run pytest tests/test_personas.py  # Persona validation
uv run pytest tests/test_config.py    # Config/preset validation
```
