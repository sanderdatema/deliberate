# Deliberators

Multi-perspectief AI deliberatie team als Claude Code skill.

## Quick Start

```bash
# Run tests
uv run pytest

# General deliberation (balanced preset, default)
/deliberate "Your question here"

# Quick analysis (3 analysts + 2 editors, 1 round)
/deliberate --preset quick "Your question here"

# Deep analysis (10 analysts + 3 editors, 2 rounds)
/deliberate --preset deep "Your question here"

# Code review (balanced code preset, default)
/deliberate-code --files src/main.py src/utils.py "Review this module"

# Quick code review (3 analysts + 1 editor, 1 round)
/deliberate-code --preset quick --files src/main.py "Security check"

# Deep code review (9 analysts + 1 editor, 2 rounds)
/deliberate-code --preset deep --files src/ "Full architecture review"

# Run via CLI (requires ANTHROPIC_API_KEY env var)
uv run python -m deliberators "Your question here" --preset balanced
uv run python -m deliberators "Review this code" --preset code_balanced --files src/main.py
```

## Presets

### General Deliberation

| Preset | Analysts | Editors | Rounds | ~Time |
|--------|----------|---------|--------|-------|
| quick | 3 (Occam, Holmes, Lupin) | 2 (Marx, Samenvatter) | 1 | ~3 min |
| balanced | 5 (Socrates, Occam, Da Vinci, Holmes, Lupin) | 3 (Marx, Hegel, Arendt) | 2 | ~5 min |
| deep | 8 (incl. Ibn Khaldun) | 3 (Marx, Hegel, Arendt) | 2 | ~8 min |

All general presets include De Samenvatter as final editor for concrete, actionable output.

### Code Review

| Preset | Analysts | Editor | Rounds | ~Time |
|--------|----------|--------|--------|-------|
| code_quick | 3 (Linus, Schneier, Hopper) | 1 (Code Synthesizer) | 1 | ~3 min |
| code_balanced | 5 (Linus, Kent Beck, Fowler, Schneier, Hopper) | 1 (Code Synthesizer) | 2 | ~5 min |
| code_deep | 9 (all code personas) | 1 (Code Synthesizer) | 2 | ~8 min |

Code personas: Linus Torvalds (code quality), Kent Beck (TDD/simplicity), Martin Fowler (architecture), Bruce Schneier (security), Steve Jobs (product vision), Don Norman (UX/API ergonomics), Jony Ive (design craft), Clayton Christensen (user-fit/JTBD), Grace Hopper (pragmatism).

## Custom Personas

Add a YAML file to `personas/` following the schema. It will be auto-loaded alongside the preset.

Required fields: `name`, `role` (analyst/editor), `reasoning_style`, `forbidden` (list, min 2), `focus`, `output_format`, `system_prompt` (must contain FORBIDDEN/MUST NOT + FORMAT YOUR RESPONSE section).

## Directory Structure

```
config.yaml             # Presets and defaults (general + code)
personas/               # Thinker definitions (YAML)
  schema.yaml           # Validation schema
  socrates.yaml         # General analysts (11)
  occam.yaml
  da-vinci.yaml
  holmes.yaml
  lupin.yaml
  templar.yaml
  tubman.yaml
  weil.yaml
  marple.yaml
  noether.yaml
  ibn-khaldun.yaml
  linus.yaml            # Code analysts (9)
  kent-beck.yaml
  fowler.yaml
  schneier.yaml
  jobs.yaml
  don-norman.yaml
  jony-ive.yaml
  christensen.yaml
  hopper.yaml
  marx.yaml             # General editors (4)
  hegel.yaml
  arendt.yaml
  samenvatter.yaml
  code-synthesizer.yaml # Code editor (1)
deliberators/           # Python engine
  engine.py             # Async orchestration engine
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
  deliberate.md         # General deliberation command
  deliberate-code.md    # Code review command
```

## Architecture

### General Deliberation (`/deliberate`)
1. Parses `--preset` flag and loads `config.yaml`
2. **Intake:** Beoordeelt of de casus helder genoeg is, vraagt door
3. Ronde 1: preset analysts spawn **in parallel** (all Opus)
4. Ronde 2: analysts react to each other (skipped in quick)
5. Editorial round: editors run **sequentially**
6. **De Samenvatter:** Concrete, alledaagse taal
7. Meta-analysis: consensus, dissensie, verschuiving

### Code Review (`/deliberate-code`)
1. Parses `--preset`, `--files` flags and loads code preset
2. **Intake:** Beoordeelt review scope, vraagt naar bestanden en focus
3. Reads specified files as code context
4. Ronde 1: code analysts review **in parallel** with code context
5. Ronde 2: analysts react to each other's reviews (skipped in quick)
6. **Code Synthesizer:** Prioritized, actionable code review
7. Meta-analysis: consensus issues, contradictions, priority fixes

## Testing

```bash
uv run pytest -v                      # All tests (500+)
uv run pytest tests/test_personas.py  # Persona validation
uv run pytest tests/test_config.py    # Config/preset validation
uv run pytest tests/test_engine.py    # Engine orchestration
uv run pytest tests/test_context.py   # Code context builder
```
