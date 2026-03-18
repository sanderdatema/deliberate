# Deliberators

Multi-perspectief AI deliberatie team als Claude Code skill.

## Quick Start

```bash
# Run tests
uv run pytest

# Use the deliberation skill
/deliberate "Your question here"
```

## Directory Structure

```
personas/           # Thinker definitions (YAML)
  schema.yaml       # Validation schema
  socrates.yaml     # Analysts (5)
  occam.yaml
  da-vinci.yaml
  holmes.yaml
  lupin.yaml
  marx.yaml         # Editors (3)
  hegel.yaml
  arendt.yaml
tests/              # Pytest validation suite
  test_personas.py  # Persona format validation
.claude/commands/   # Claude Code slash commands
  deliberate.md     # Main orchestration command
```

## Persona Format

Each persona is a YAML file with:
- `name`: Display name
- `role`: `analyst` or `editor`
- `reasoning_style`: One-line description
- `forbidden`: List of hard constraints (things this thinker MUST NOT do)
- `focus`: What this thinker zeroes in on
- `output_format`: Which output fields are enabled
- `system_prompt`: Full prompt with FORBIDDEN/MUST NOT constraints

## Architecture

1. `/deliberate` slash command receives question
2. 5 analyst agents spawn **in parallel** (all Opus)
3. 3 editor agents run **sequentially**, each seeing all prior output
4. Orchestrator compiles final report with meta-analysis

## Testing

```bash
uv run pytest -v                    # All tests
uv run pytest tests/test_personas.py  # Persona validation only
```
