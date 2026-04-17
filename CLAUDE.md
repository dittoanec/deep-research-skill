# Titan Research Kit

A unified research skill set providing three capabilities:

1. **Deep Research** — Multi-pass ARCHITECT→MINER→CHALLENGER→COMPILER pipeline for evidence-based, decision-ready research
2. **Eval Loop** — Claude-as-judge with configurable rubrics + bottom-quartile regeneration with feedback injection
3. **Brainstorm** — Novel angle generation that pushes beyond obvious framings

## Two Integration Modes

### Claude CLI (skill-based)
Skills live in `skills/*/SKILL.md`. The master router at `.claude/skills/titan-research.md` auto-detects which skill to invoke based on the user's request.

```bash
# Add to any project:
claude skill add /path/to/titan-research-kit
```

### Python / Nova (programmatic)
```python
from titan_research_kit.research import ResearchOrchestrator
from titan_research_kit.eval import EvalLoop, RESEARCH_RUBRIC
from titan_research_kit.brainstorm import brainstorm_angles
```

## CLI

```bash
python -m titan_research_kit research "What is the best approach to X?"
python -m titan_research_kit brainstorm --domain "content creation" --topics topic1,topic2
python -m titan_research_kit eval --input outputs/*.txt --rubric research --regen-bottom 0.25
```

## Structure

```
titan-research-kit/
├── skills/               # Claude CLI skill definitions (SKILL.md per capability)
│   ├── deep-research/
│   ├── eval-loop/
│   └── brainstorm/
├── agents/               # Claude CLI agent profiles
├── titan_research_kit/   # Python package
│   ├── research/         # Deep research engine
│   ├── eval/             # Eval loop engine
│   ├── brainstorm/       # Brainstorm engine
│   └── prompts/          # System prompts (shared)
└── .claude/skills/       # Master router skill
```

## Environment Variables

```
ANTHROPIC_API_KEY=           # Required
MODEL=claude-sonnet-4-20250514
FALLBACK_MODEL=claude-haiku-4-5-20251001
```
