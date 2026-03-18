# Deliberators

Multi-perspective AI deliberation — a team of virtual thinkers debates complex questions from diverse perspectives, producing deeper, more nuanced answers than any single AI response.

Inspired by Martijn Aslander's "Magische Dertien" and Scott Page's Diversity Prediction Theorem: collective error = average individual error **minus** diversity of predictions.

## How It Works

Deliberators assembles a team of AI personas — each with a distinct reasoning style, domain expertise, and set of forbidden shortcuts — and orchestrates a structured debate. The result is a thematic synthesis report with landscape analysis, tensions, blind spots, and concrete action items.

### Pipeline

1. **Intake** — Assesses whether the question is clear enough; asks follow-up questions if needed
2. **Team Selection** — Picks the optimal team from a 25-persona pool based on domain match and gender balance (>=40% M/F)
3. **Team Approval** — Shows the proposed team with per-persona motivation; you can adjust before starting
4. **Round 1** — All analysts work in parallel, independently
5. **Convergence Check** — Decides whether another round would add value
6. **Round 2+** — Analysts react to each other's positions (adaptive, stops at consensus)
7. **Editorial** — Editors identify blind spots and synthesize (sequential)
8. **De Samenvatter** — Translates everything into concrete, everyday language
9. **Synthesis** — Thematic report: Landscape, Tensions, Blind Spots, Shifts, Action Items

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI (installed and authenticated)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

## Installation

### Step 1: Clone the repository

```bash
git clone https://github.com/sanderdatema/deliberate.git ~/.claude/skills/deliberate
```

### Step 2: Install the Python package

Using uv (recommended):
```bash
cd ~/.claude/skills/deliberate
uv tool install .
```

Or using pip:
```bash
cd ~/.claude/skills/deliberate
pip install .
```

### Step 3: Add the slash command to Claude Code

```bash
cp ~/.claude/skills/deliberate/.claude/commands/deliberate.md ~/.claude/commands/deliberate.md
```

### Verify installation

```bash
# Check the package is importable
python3 -c "from deliberators.loader import ConfigLoader; print('OK')"

# In Claude Code, run a quick test
/deliberate --preset quick "What are the tradeoffs of microservices vs monolith?"
```

### Updating

```bash
cd ~/.claude/skills/deliberate
git pull
uv tool install . --force   # or: pip install . --force-reinstall
cp .claude/commands/deliberate.md ~/.claude/commands/deliberate.md
```

## Usage

All usage is through the `/deliberate` slash command inside Claude Code:

```bash
# Standard deliberation (balanced preset)
/deliberate "Should our company switch to a four-day work week?"

# Quick analysis (3 analysts, 1 round, ~3 min)
/deliberate --preset quick "What are the risks of our new marketing strategy?"

# Deep analysis (8 analysts, max 3 rounds, ~8 min)
/deliberate --preset deep "How should we approach our AI strategy for the next 5 years?"

# Code review (team selector picks code-focused personas automatically)
/deliberate --files src/main.py src/utils.py "Review this module for quality and security"

# Follow-up on a previous deliberation
/deliberate --followup <decision-id> "What about the cost implications?"
```

## Presets

Teams are dynamically assembled based on the question. Presets control team size and depth:

| Preset | Analysts | Editors | Rounds | ~Time |
|--------|----------|---------|--------|-------|
| `quick` | 3 | 1 | 1 | ~3 min |
| `balanced` | 5 | 2 | 1-2 | ~5 min |
| `deep` | 8 | 3 | 1-3 | ~8 min |

De Samenvatter is always the final editor, ensuring concrete and actionable output.

## Persona Pool

25 personas (20 analysts, 5 editors) across 6 domains:

- **Code & Architecture** — Fowler, Kent Beck, Linus, Margaret Hamilton, Schneier, Barbara Liskov
- **Problem Framing & Thinking** — Socrates, Occam, Kahneman, Taleb
- **Product & User** — Don Norman, Jobs, Virginia Apgar
- **Creative & Narrative** — Jony Ive, Lupin, Hedy Lamarr, Scheherazade, Shakespeare
- **Systems & Society** — Donella Meadows, Elizabeth Bennet
- **Editors** — Marx, Hegel, Arendt, De Samenvatter, Code Synthesizer

29 additional archived personas are available in `personas/archived/` for re-activation.

### Custom Personas

Add a YAML file to `personas/` and it will be auto-discovered. Required fields:

- `name`, `model`, `domains`, `role` (analyst/editor)
- `reasoning_style`, `forbidden` (list, min 2), `focus`, `output_format`
- `system_prompt` (must contain FORBIDDEN/MUST NOT + FORMAT YOUR RESPONSE sections)

See `personas/schema.yaml` for the full validation schema.

## Configuration

Deliberators looks for configuration in this order:

1. Explicit path via CLI argument
2. `./config.yaml` in the current directory
3. `~/.config/deliberators/config.yaml`
4. Bundled defaults (shipped with the package)

The same resolution applies to personas. You can override the bundled personas by placing YAML files in `~/.config/deliberators/personas/`.

## Decision History

All deliberation results are automatically saved to `~/.local/share/deliberators/decisions/` as JSON files. Use `--followup <id>` to build on a previous deliberation.

## Architecture

```
config.yaml              # Presets and defaults
personas/                # 25 active persona definitions (YAML)
  archived/              # 29 archived personas
  schema.yaml            # Persona validation schema
deliberators/
  engine.py              # Async orchestration + team selection
  prompts.py             # Pure prompt builders (analyst, editor, catalog)
  models.py              # Dataclasses (Persona, Config, DecisionRecord, ...)
  loader.py              # YAML loaders + path resolution
  storage.py             # DecisionStore (JSON save/load/list)
  formatter.py           # Thematic report formatter
  context.py             # CodeContextBuilder (code review file injection)
  web_pusher.py          # HTTP push client for web viewer
  web/                   # FastAPI WebSocket live viewer
  __main__.py            # CLI entry point (disabled by default)
tests/                   # Pytest test suite (736 tests)
.claude/commands/
  deliberate.md          # Claude Code slash command definition
```

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run specific test modules
uv run pytest tests/test_personas.py   # Persona validation
uv run pytest tests/test_engine.py     # Engine orchestration
uv run pytest tests/test_prompts.py    # Prompt builders
```

## Standalone CLI (Advanced)

The primary interface is the Claude Code `/deliberate` command. For advanced users who want to run deliberations from the terminal directly, a CLI is available but disabled by default:

```bash
DELIBERATORS_ALLOW_CLI=1 python -m deliberators "Your question" --preset balanced
```

This requires the `claude` CLI to be available on your PATH, as each persona runs as a separate `claude -p` subprocess.

## License

MIT License. See [LICENSE](LICENSE) for details.
