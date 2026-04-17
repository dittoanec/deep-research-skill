# Titan Research Kit — Master Skill Router

This project provides three research skills. Use the appropriate one based on the user's request.

## Skill Routing

### → Deep Research (`skills/deep-research/SKILL.md`)
**Trigger signals:** "research X", "deep dive into", "compare options for", "evaluate approaches to", "what's the best way to", "decision-ready analysis"

Use the full ARCHITECT → MINER → CHALLENGER → COMPILER pipeline. This is for questions where being wrong is costly and you need structured, evidence-based output.

### → Eval Loop (`skills/eval-loop/SKILL.md`)
**Trigger signals:** "evaluate these", "judge this batch", "score these outputs", "improve quality", "regen the weak ones", "quality gate", "which of these are best"

Use when you have a batch of generated outputs and need to systematically judge, rank, and improve them. Pick the rubric preset that matches the content type, or let the user define a custom rubric.

### → Brainstorm (`skills/brainstorm/SKILL.md`)
**Trigger signals:** "brainstorm angles", "novel ideas for", "creative framings", "non-obvious approaches", "what else could we try", "expand the idea space"

Use when the user needs divergent thinking — novel angles that go beyond what retrieval or obvious reasoning would produce.

### → Full Pipeline (chain all three)
**Trigger signals:** "full research pipeline", "research and validate", "thorough analysis with quality check"

Chain: Deep Research → Brainstorm (expand scope) → Eval Loop (quality-gate findings)

## Agent Profiles
When spawning sub-agents for the deep research skill, use the corresponding agent profile from `agents/`:
- `agents/researcher.md` — for MINER phase
- `agents/challenger.md` — for CHALLENGER phase
- `agents/compiler.md` — for COMPILER phase
- `agents/judge.md` — for eval loop judging
