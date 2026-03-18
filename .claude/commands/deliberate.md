---
description: "Multi-perspectief deliberatie over een vraagstuk door een team van AI-denkers"
---

CRITICAL INSTRUCTION: Invoke the `deliberate` skill via the Skill tool NOW (if not already done). Once the skill is loaded, follow its task instructions — do NOT call the Skill tool again. The skill tells you to orchestrate using Read, AskUserQuestion, and Agent tools directly. You are the orchestrator, not a persona.

If you cannot invoke the Skill tool, tell the user: "De /deliberate skill kan niet worden uitgevoerd. Start een nieuwe sessie."

Do NOT:
- Generate philosophical questions and answers yourself
- Pretend to be multiple personas
- Create a "deliberation-like" response without the actual skill
- Run this in the background — the report must be shown directly to the user

## Context Gathering (BEFORE invoking the skill)

Before invoking the Skill tool, assess whether the question relates to the current project/codebase. If it does:

1. **Read the project's CLAUDE.md** to understand the project structure, tech stack, and conventions
2. **Read relevant source files** that the question touches on (architecture files, config, key modules)
3. **Summarize this context** and prepend it to the arguments as `[PROJECT CONTEXT: ...]`

Examples of questions that need project context:
- "How should we structure the API?" → read the current API code, routes, models
- "Is our auth approach secure?" → read auth middleware, config, dependencies
- "Should we refactor the database layer?" → read DB models, queries, migrations
- "Review the architecture" → read main entry points, key modules, directory structure

The agent team has NO access to the codebase unless you provide context. Without it, they give generic advice instead of project-specific insights. This is the #1 cause of bad deliberation output.

The user's arguments: $ARGUMENTS
