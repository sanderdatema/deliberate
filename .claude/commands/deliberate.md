---
description: "Multi-perspectief deliberatie over een vraagstuk door een team van AI-denkers"
---

# Deliberate: Multi-Agent Reasoning Team

You are the orchestrator of a deliberation team. Your job is to coordinate a team of thinkers — each with their own reasoning style and hard constraints — to analyze a question from multiple perspectives, then have editorial analysts identify blind spots and synthesize insights.

## Input

The user's question: $ARGUMENTS

## Step 1: Load Personas

Read all YAML files from the `personas/` directory (excluding `schema.yaml`). Each file defines a thinker with:
- `name`: Display name
- `role`: "analyst" or "editor"
- `system_prompt`: The full prompt for this thinker
- `reasoning_style`: One-line description of their approach

Separate them into two groups:
- **Analysts** (role: analyst): Socrates, Occam, Da Vinci, Holmes, Lupin
- **Editors** (role: editor): Marx, Hegel, Arendt

## Step 2: Analyst Round (Parallel)

Spawn ALL analyst agents **in parallel** using the Agent tool. For each analyst:

- Use the Agent tool with `model: "opus"`
- Set `description` to the persona name (e.g., "Socrates analyzes question")
- Set `name` to the persona name lowercased (e.g., "socrates")
- The `prompt` should be:

```
{system_prompt from YAML}

---

QUESTION FOR DELIBERATION:
{$ARGUMENTS}

---

Provide your analysis following your role's output structure. Be thorough but focused.
Stay strictly within your reasoning constraints — they are not suggestions, they are absolute rules.
```

**IMPORTANT**: Launch all 5 analyst agents in a SINGLE message with multiple Agent tool calls. This ensures true parallel execution.

## Step 3: Collect Analyst Output

After all analysts have responded, compile their output into a single document:

```
## Analyst Perspectives

### Socrates (Dialectische ondervrager)
{socrates output}

### Willem van Occam (Radicale snoeier)
{occam output}

### Leonardo da Vinci (Cross-domein patroonzoeker)
{da-vinci output}

### Sherlock Holmes (Deductieve bewijs-jager)
{holmes output}

### Arsène Lupin (Contraire omdraaier)
{lupin output}
```

## Step 4: Editorial Round (Sequential)

Spawn editor agents ONE AT A TIME, sequentially. Each editor receives all prior output.

### Editor 1: Karl Marx
Spawn with Agent tool (`model: "opus"`):
```
{marx system_prompt}

---

ORIGINAL QUESTION:
{$ARGUMENTS}

ANALYST PERSPECTIVES:
{compiled analyst output from Step 3}

---

Analyze the collective output. What did NOBODY question? What assumptions do ALL analysts share?
```

### Editor 2: Georg Hegel
Spawn with Agent tool (`model: "opus"`), including Marx's output:
```
{hegel system_prompt}

---

ORIGINAL QUESTION:
{$ARGUMENTS}

ANALYST PERSPECTIVES:
{compiled analyst output from Step 3}

PRIOR EDITORIAL ANALYSIS:
### Karl Marx
{marx output}

---

Find the Aufhebung. What synthesis transcends the contradictions between analysts?
```

### Editor 3: Hannah Arendt
Spawn with Agent tool (`model: "opus"`), including all prior editor output:
```
{arendt system_prompt}

---

ORIGINAL QUESTION:
{$ARGUMENTS}

ANALYST PERSPECTIVES:
{compiled analyst output from Step 3}

PRIOR EDITORIAL ANALYSIS:
### Karl Marx
{marx output}

### Georg Hegel
{hegel output}

---

Uncover the mechanisms. WHY were these specific blind spots produced? What about how we think caused these gaps?
```

## Step 5: Format Final Report

Present the complete deliberation as a structured markdown report:

```markdown
# Deliberation: {$ARGUMENTS}

## Analyst Perspectives

### Socrates — Dialectische ondervrager
{socrates output}

### Willem van Occam — Radicale snoeier
{occam output}

### Leonardo da Vinci — Cross-domein patroonzoeker
{da-vinci output}

### Sherlock Holmes — Deductieve bewijs-jager
{holmes output}

### Arsène Lupin — Contraire omdraaier
{lupin output}

---

## Editorial Analysis

### Karl Marx — Collectieve blinde-vlek-detector
{marx output}

### Georg Hegel — Dialectische synthesizer
{hegel output}

### Hannah Arendt — Mechanisme-ontdekker
{arendt output}

---

## Meta-Analyse

Synthesize the entire deliberation into a brief conclusion:
- **Consensus**: Where do the analysts converge?
- **Dissensie**: Where do they fundamentally disagree?
- **Blinde vlekken**: What did the editors uncover that nobody saw?
- **Vraagverschuiving**: How has the original question transformed?
- **Kernvraag**: What is the REAL question that should be asked?
```

## Important Notes

- Each agent operates independently — they cannot see each other's output during the analyst round
- Editors see ALL analyst output and prior editor output
- The meta-analyse at the end is YOUR synthesis as orchestrator, not another agent's
- If any agent fails, report it and continue with the remaining perspectives
- The entire deliberation should take ~2-3 minutes with parallel analyst execution
