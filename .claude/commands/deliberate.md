---
description: "Multi-perspectief deliberatie over een vraagstuk door een team van AI-denkers"
---

# Deliberate: Multi-Agent Reasoning Team

You are the orchestrator of a deliberation team. Your job is to coordinate a team of thinkers — each with their own reasoning style and hard constraints — to analyze a question from multiple perspectives across two rounds, then have editorial analysts identify blind spots and synthesize insights.

## Input

The user's arguments: $ARGUMENTS

Parse $ARGUMENTS for flags:
- If `--preset quick` is present: use the "quick" preset, remove the flag from the question
- If `--preset deep` is present: use the "deep" preset, remove the flag from the question
- If `--preset balanced` is present or no flag: use the "balanced" preset
- If `--web` is present: enable live web viewer (see Web Viewer Integration below)
- Everything remaining after stripping flags is the **question**

## Web Viewer Integration

If `--web` flag is present:

1. **Check the viewer server is running** via Bash:
   ```
   curl -s http://localhost:8000/api/latest-session
   ```
   If this fails, tell the user: "Start de web viewer eerst in een apart terminal: `uv run python -m deliberators.web`" and STOP.

2. **Create a session** via Bash:
   ```
   curl -s -X POST http://localhost:8000/api/session | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])"
   ```
   Store the returned session ID.

3. Display to the user:
   ```
   Web viewer: http://localhost:8000
   Open in je browser om live mee te kijken.
   ```

4. **Throughout the deliberation**, push events after each significant step using Bash:
   - After starting deliberation: `curl -s -X POST http://localhost:8000/api/events/{SESSION_ID} -H 'Content-Type: application/json' -d '{"type":"deliberation_started"}'`
   - After starting a round: `curl -s -X POST ... -d '{"type":"round_started","round_number":N}'`
   - Before spawning each agent: `curl -s -X POST ... -d '{"type":"agent_started","agent_name":"NAME","round_number":N}'`
   - After each agent completes: `curl -s -X POST ... -d '{"type":"agent_completed","agent_name":"NAME","round_number":N}'`
   - Push text output: `curl -s -X POST ... -d '{"type":"text_delta","agent_name":"NAME","text":"OUTPUT"}'`
   - After editorial starts/ends: push editorial_started/editorial_completed
   - After completion: push `{"type":"result","markdown":"..."}` and then POST to `/api/events/{SESSION_ID}/done`

5. **Batch text pushing**: After each agent completes, push their FULL output as one text_delta (not streaming — Claude Code agents return complete output). This is simpler and still gives the viewer useful real-time progress as agents finish.

If `--web` is NOT present: skip all curl calls, run normally as before.

## Step 0: Intake — Beoordeel de casus en vraag door

**BEFORE doing anything else**, assess whether the user's question is clear and complete enough to deliberate on. A good casus needs:

1. **Helder vraagstuk:** Is duidelijk wat er beantwoord of onderzocht moet worden?
2. **Voldoende context:** Zijn de relevante omstandigheden, betrokkenen, en beperkingen beschreven?
3. **Geen cruciale gaten:** Zijn er voor de hand liggende vragen waarvan het antwoord de analyse fundamenteel zou veranderen?

**If the casus is unclear or incomplete:**

Use the AskUserQuestion tool to ask ONE clarifying question at a time. Focus on the most critical gap first. Examples of good intake questions:
- "Wat is het concrete resultaat dat je wilt bereiken met dit gesprek?"
- "Wie zijn de belangrijkste betrokkenen, en wat is hun onderlinge relatie?"
- "Is er al iets geprobeerd, en zo ja, wat was het effect?"
- "Wat is je tijdshorizon — heb je morgen een antwoord nodig of is dit een langetermijnvraag?"

Ask a maximum of 12 questions total (one at a time, wait for each answer). After each answer, reassess: is the casus now clear enough? Most cases will need 2-5 questions; complex cases may need more.

**If the casus is clear enough:** Proceed to Step 1. Display: `Casus helder. Deliberatie wordt gestart.`

**IMPORTANT:** Do NOT fill in missing context with assumptions. If you don't know something, ASK. The whole point of the intake is to prevent the analysts from making up context that may be wrong.

## Step 1: Load Configuration & Personas

1. Read `config.yaml` from the project root. It defines presets with analyst/editor lists and round counts.

2. Based on the selected preset, determine:
   - Which analyst persona files to load (by filename without .yaml)
   - Which editor persona files to load
   - How many rounds to run

3. Read only the YAML files listed in the preset from `personas/` directory.

4. **Custom persona support:** After loading preset personas, check if any additional .yaml files exist in `personas/` that are NOT in the standard 14 (socrates, occam, da-vinci, holmes, lupin, templar, tubman, weil, marple, noether, marx, hegel, arendt, samenvatter) and NOT schema.yaml. If found, validate they have the required fields (name, role, system_prompt, forbidden) and add them as extra analysts or editors based on their role. Display: `Custom persona geladen: {name}`

5. Display the configuration:
```
Deliberatie gestart met preset: {preset_name}
Analisten: {count} | Editors: {count} | Rondes: {rounds}
```

**Preset reference:**
- **quick:** 3 analysts (Occam, Holmes, Lupin) + 2 editors (Marx, Samenvatter), 1 round
- **balanced:** 5 analysts (Socrates, Occam, Da Vinci, Holmes, Lupin) + 3 editors (Marx, Hegel, Arendt), 2 rounds
- **deep:** 10 analysts (all) + 3 editors (all), 2 rounds

## Step 2: Ronde 1 — Onafhankelijke Analyse (Parallel)

Display: `## Ronde 1: Onafhankelijke Analyse`

Spawn ALL **preset** analyst agents **in parallel** using the Agent tool. For each analyst:

- Use the Agent tool with `model: "opus"`
- Set `description` to the persona name (e.g., "Socrates analyzes question")
- Set `name` to the persona name lowercased (e.g., "socrates-r1")
- The `prompt` should be:

```
{system_prompt from YAML}

---

QUESTION FOR DELIBERATION:
{$ARGUMENTS}

---

Provide your analysis following your role's output structure. Be thorough but focused.
Stay strictly within your reasoning constraints — they are not suggestions, they are absolute rules.
Respond in the same language as the question.
```

**IMPORTANT**: Launch all 5 analyst agents in a SINGLE message with multiple Agent tool calls. This ensures true parallel execution.

## Step 3: Compile Ronde 1 Summary

After all analysts respond, compile a concise summary (key positions only, not full text):

```
RONDE 1 SAMENVATTING:

Socrates: [1-2 sentence core of their challenges/questions]
Occam: [Position + confidence score]
Da Vinci: [Core pattern identified + confidence]
Holmes: [Key deduction + confidence]
Lupin: [Inverted position + confidence]
```

## Step 4: Ronde 2 — Reactieve Deliberatie (Parallel)

**SKIP this step entirely if the preset has rounds: 1 (e.g., "quick" preset).**

Display: `## Ronde 2: Reactieve Deliberatie`

Spawn ALL preset analyst agents again **in parallel**. This time each receives the Round 1 summary. For each analyst:

- Use the Agent tool with `model: "opus"`
- Set `name` to the persona name lowercased (e.g., "socrates-r2")
- The `prompt` should be:

```
{system_prompt from YAML}

---

QUESTION FOR DELIBERATION:
{$ARGUMENTS}

THIS IS ROUND 2. You have seen what the other thinkers said in Round 1. React to their perspectives while maintaining your constraints. You may sharpen, challenge, or revise your position. Specifically address the strongest point that contradicts your approach.

ROUND 1 PERSPECTIVES:
{compiled Round 1 summary from Step 3}

---

Provide your Round 2 analysis. Explain how the other perspectives have (or have not) affected your thinking. Stay strictly within your reasoning constraints.
Respond in the same language as the question.
```

**IMPORTANT**: Launch all 5 analyst agents in a SINGLE message. True parallel execution.

## Step 5: Editorial Round (Sequential)

Display: `## Redactionele Analyse`

Compile ALL output from both rounds into a combined analyst document. Then spawn editor agents ONE AT A TIME, sequentially. Each editor receives all prior output.

### Editor 1: Karl Marx
Spawn with Agent tool (`model: "opus"`):
```
{marx system_prompt}

---

ORIGINAL QUESTION:
{$ARGUMENTS}

ANALYST PERSPECTIVES (ROUND 1 + ROUND 2):
{compiled output from both rounds — for each analyst, show their Round 1 and Round 2 positions}

---

Analyze the collective output across both rounds. What did NOBODY question? What assumptions do ALL analysts share even after seeing each other's work?
Respond in the same language as the question.
```

### Editor 2: Georg Hegel
Spawn with Agent tool (`model: "opus"`), including Marx's output:
```
{hegel system_prompt}

---

ORIGINAL QUESTION:
{$ARGUMENTS}

ANALYST PERSPECTIVES (ROUND 1 + ROUND 2):
{compiled analyst output from both rounds}

PRIOR EDITORIAL ANALYSIS:
### Karl Marx
{marx output}

---

Find the Aufhebung. What synthesis transcends the contradictions? Pay special attention to how positions shifted between rounds.
Respond in the same language as the question.
```

### Editor 3: Hannah Arendt
Spawn with Agent tool (`model: "opus"`), including all prior editor output:
```
{arendt system_prompt}

---

ORIGINAL QUESTION:
{$ARGUMENTS}

ANALYST PERSPECTIVES (ROUND 1 + ROUND 2):
{compiled analyst output from both rounds}

PRIOR EDITORIAL ANALYSIS:
### Karl Marx
{marx output}

### Georg Hegel
{hegel output}

---

Uncover the mechanisms. WHY were these specific blind spots produced? What about how the group thinks caused these gaps? Consider what changed (and what didn't) between rounds.
Respond in the same language as the question.
```

## Step 6: Samenvatter — Maak het concreet

After all editors are done, spawn ONE final agent: the Samenvatter. This agent reads the ENTIRE deliberation (all rounds + all editors + your meta-analysis) and distills it into a concrete, everyday-language summary that the user can directly act on.

Load the samenvatter persona from `personas/samenvatter.yaml` and spawn with Agent tool (`model: "opus"`):

```
{samenvatter system_prompt}

---

ORIGINAL QUESTION:
{$ARGUMENTS}

FULL DELIBERATION OUTPUT:
{everything: all analyst rounds, all editor analyses}

---

Distill this entire deliberation into concrete, actionable advice. Write as if you're talking to a friend over coffee. No jargon, no academic language. What should this person actually DO?
Respond in the same language as the question.
```

Display the samenvatter output as:
```markdown
---

## Kort & Concreet

{samenvatter output}
```

## Step 7: Format Full Report (collapsible)

Present the complete deliberation as a structured markdown report:

```markdown
# Deliberatie: {$ARGUMENTS}

## Ronde 1: Onafhankelijke Analyse

### Socrates — Dialectische ondervrager
{socrates round 1 output}

### Willem van Occam — Radicale snoeier
{occam round 1 output}

### Leonardo da Vinci — Cross-domein patroonzoeker
{da-vinci round 1 output}

### Sherlock Holmes — Deductieve bewijs-jager
{holmes round 1 output}

### Arsène Lupin — Contraire omdraaier
{lupin round 1 output}

---

## Ronde 2: Reactieve Deliberatie

### Socrates — Reactie
{socrates round 2 output}

### Willem van Occam — Reactie
{occam round 2 output}

### Leonardo da Vinci — Reactie
{da-vinci round 2 output}

### Sherlock Holmes — Reactie
{holmes round 2 output}

### Arsène Lupin — Reactie
{lupin round 2 output}

---

## Redactionele Analyse

### Karl Marx — Collectieve blinde-vlek-detector
{marx output}

### Georg Hegel — Dialectische synthesizer
{hegel output}

### Hannah Arendt — Mechanisme-ontdekker
{arendt output}

---

## Consensus & Dissensie

### Convergentie
[Points where 3+ analysts agree, with their confidence scores]

### Polarisatie
[Points where analysts fundamentally disagree]

### Verschuiving Ronde 1 → 2
[How positions changed between rounds — who moved, who held firm, and why]

### Vraagverschuiving
[The most powerful question shifts from the editors]

### Gewogen Conclusie
[Weighted summary: what emerges when you combine the confidence scores, the consensus points, the editorial blind spots, and the round-over-round shifts into a single coherent picture]
```

## Important Notes

- Each agent operates independently within a round — they cannot see each other during parallel execution
- Round 2 agents see Round 1 output but NOT other Round 2 agents' output
- Editors see ALL output from both rounds and prior editors
- The meta-analyse sections (Consensus & Dissensie) are YOUR synthesis as orchestrator
- If any agent fails, report it and continue with remaining perspectives
- All agents use model "opus" for deep reasoning
- The entire deliberation takes ~5-8 minutes with parallel execution per round
