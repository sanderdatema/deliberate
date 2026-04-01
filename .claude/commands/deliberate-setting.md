---
description: "Beheer persoonlijke voorkeuren voor deliberaties (toon, stijl, team)"
---

Manage the user's deliberation preferences stored in `~/.local/share/deliberators/preferences.json`.

These preferences are injected as HIGH PRIORITY constraints into every deliberation — they influence team selection, analyst tone, and report style.

## Parse Arguments

The arguments: $ARGUMENTS

### No arguments → List preferences

Read `~/.local/share/deliberators/preferences.json`. If it doesn't exist or is empty, say:
"Geen voorkeuren ingesteld. Gebruik `/deliberate-setting <voorkeur>` om er een toe te voegen."

Otherwise, display as a numbered list:
```
Deliberatie-voorkeuren:
1. Niet paternalistisch
2. Geef concrete voorbeelden, geen abstracte principes
```

### `--remove N` → Remove preference

Remove the Nth preference (1-indexed) from the list. Save the updated list. Confirm what was removed.

### `--clear` → Remove all preferences

Clear all preferences. Ask for confirmation first via AskUserQuestion.

### Any other text → Add preference

Add the text as a new preference. Save to `~/.local/share/deliberators/preferences.json`.

**Format:**
```json
{
  "preferences": [
    "Niet paternalistisch",
    "Geef concrete voorbeelden, geen abstracte principes"
  ]
}
```

Ensure the directory exists before writing. Confirm what was added and show the current list.

## Examples

- `/deliberate-setting` → show current preferences
- `/deliberate-setting Niet paternalistisch` → add preference
- `/deliberate-setting Gebruik humor waar gepast` → add preference
- `/deliberate-setting --remove 1` → remove first preference
- `/deliberate-setting --clear` → remove all
