# Deliberators

Multi-perspectief AI deliberatie team als Claude Code skill.

## Quick Start

```bash
# Run tests
uv run pytest

# Use the deliberation skill (balanced preset, default)
/deliberate "Your question here"

# Quick analysis (3 analysts + 1 editor, 1 round)
/deliberate --preset quick "Your question here"

# Deep analysis (10 analysts + 3 editors, 2 rounds)
/deliberate --preset deep "Your question here"
```

## Presets

| Preset | Analysts | Editors | Rounds | ~Time |
|--------|----------|---------|--------|-------|
| quick | 3 (Occam, Holmes, Lupin) | 1 (Marx) | 1 | ~3 min |
| balanced | 5 (Socrates, Occam, Da Vinci, Holmes, Lupin) | 3 (Marx, Hegel, Arendt) | 2 | ~5 min |
| deep | 10 (all) | 3 (all) | 2 | ~10 min |

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
  templar.yaml          # Analysts — extended 5
  tubman.yaml
  weil.yaml
  marple.yaml
  noether.yaml
  marx.yaml             # Editors (3)
  hegel.yaml
  arendt.yaml
tests/                  # Pytest validation suite
  test_personas.py      # Persona format validation (159 tests)
  test_config.py        # Config and preset validation
.claude/commands/       # Claude Code slash commands
  deliberate.md         # Main orchestration command
```

## Architecture

1. `/deliberate` parses `--preset` flag and loads `config.yaml`
2. Ronde 1: preset analysts spawn **in parallel** (all Opus)
3. Ronde 2: analysts react to each other's Round 1 output (skipped in quick)
4. Editorial round: editors run **sequentially** with accumulated context
5. Meta-analysis: consensus, dissensie, verschuiving, gewogen conclusie

## Testing

```bash
uv run pytest -v                      # All tests
uv run pytest tests/test_personas.py  # Persona validation
uv run pytest tests/test_config.py    # Config/preset validation
```
