# 🔬 Titan Research Kit

A unified research skill set for AI coding agents. Three capabilities, one toolkit — usable from both **Claude CLI** (skill-based) and **Python/Nova** (programmatic).

## Capabilities

### 1. Deep Research
Multi-pass **ARCHITECT → MINER → CHALLENGER → COMPILER** pipeline that produces decision-ready output with typed claims, evidence tiers, and adversarial review.

- Decomposes questions into MECE sub-questions
- Gathers structured, falsifiable claims with source attribution
- Adversarial Challenger red-teams every finding
- Compiles into BLUF report with Decision Matrix and NOW/NEXT/NEVER actions

### 2. Eval Loop
**Judge → Rank → Regenerate → Re-judge** cycle that systematically improves batch quality. Configurable rubrics with built-in presets.

- Score outputs on N axes (0-5 each) using Claude-as-judge
- Rank by total score, regenerate bottom N% with feedback injection
- Re-judge to measure lift — proves the loop works quantitatively
- Compound iteration (run 2-3 passes for diminishing-returns optimization)

### 3. Brainstorm
Novel angle generator that pushes beyond what RAG or obvious reasoning produces. Anti-cliché guards enforce genuine diversity.

- Bans the 3 most obvious angles before generating
- Enforces diversity across life contexts (domestic, creative, physical, philosophical)
- Each angle includes concrete details that seed full content pieces
- Domain-agnostic — works for any content type, not just anecdotes

## Quick Start

### Installation

```bash
git clone https://github.com/davidyseo/titan-research-kit.git
cd titan-research-kit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...
```

### Claude CLI

```bash
# Add the skill to any project
claude skill add /path/to/titan-research-kit

# Then ask naturally — the master router picks the right skill:
# "Do deep research on X"        → deep-research
# "Judge these outputs"           → eval-loop  
# "Brainstorm angles for Y"      → brainstorm
```

### Python / Nova

```python
from titan_research_kit.research import ResearchOrchestrator
from titan_research_kit.eval import EvalLoop, CONTENT_RUBRIC
from titan_research_kit.brainstorm import brainstorm_angles

# Deep research
report = ResearchOrchestrator().run("What is the best approach to X?")

# Eval loop
loop = EvalLoop(rubric=CONTENT_RUBRIC)
results = loop.run(["item 1 text", "item 2 text", ...])
print(f"Lift: {results.avg_lift:+.2f}")

# Brainstorm
angles = brainstorm_angles(
    domain="blog posts",
    topics={"ai_ethics": {"keywords": ["bias", "fairness"], "emotional_arc": "tension → resolution"}},
    per_topic=15,
)
```

### CLI

```bash
# Deep research
python -m titan_research_kit research "What is the best database for time-series data?"

# Brainstorm
python -m titan_research_kit brainstorm --domain "content creation" --topics ai,leadership --per-topic 10

# Eval loop
python -m titan_research_kit eval --input outputs.txt --rubric content --regen-bottom 0.25
```

## Rubric Presets

The eval loop ships with three built-in rubrics:

| Preset | Axes | Best For |
|--------|------|----------|
| `content` | voice_match, specificity, novelty, emotional_resonance | Articles, anecdotes, social posts |
| `research` | accuracy, evidence_quality, balance, actionability | Research claims, analysis |
| `code` | correctness, readability, efficiency, robustness | Code review, generated code |

Custom rubrics:
```python
from titan_research_kit.models import JudgeRubric, JudgeAxis

MY_RUBRIC = JudgeRubric(
    name="tweets",
    axes=[
        JudgeAxis(name="hook", description="Does the first line stop the scroll?", weight=2.0),
        JudgeAxis(name="clarity", description="Is the point immediately clear?", weight=1.0),
        JudgeAxis(name="shareability", description="Would someone RT this?", weight=1.5),
    ],
)
```

## Project Structure

```
titan-research-kit/
├── .claude/skills/              # Master router skill
│   └── titan-research.md
├── skills/                      # Claude CLI skill definitions
│   ├── deep-research/SKILL.md
│   ├── eval-loop/SKILL.md
│   └── brainstorm/SKILL.md
├── agents/                      # Agent profiles
│   ├── researcher.md
│   ├── challenger.md
│   ├── compiler.md
│   └── judge.md
└── titan_research_kit/          # Python package
    ├── config.py                # Unified configuration
    ├── models.py                # Pydantic data models
    ├── cli.py                   # CLI entry point
    ├── research/                # Deep research engine
    │   ├── orchestrator.py      # Multi-pass loop controller
    │   └── agents/              # Researcher, Challenger, Compiler
    ├── eval/                    # Eval loop engine
    │   ├── judge.py             # Configurable rubric judge
    │   ├── regenerator.py       # Feedback-injected regeneration
    │   ├── loop.py              # Judge→Rank→Regen→Rejudge orchestrator
    │   └── rubrics.py           # Built-in presets
    ├── brainstorm/              # Brainstorm engine
    │   └── angles.py            # Novel angle generator
    └── prompts/                 # System prompts (shared)
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | — | Anthropic API key |
| `MODEL` | — | `claude-sonnet-4-20250514` | Default model |
| `FALLBACK_MODEL` | — | `claude-haiku-4-5-20251001` | Fallback model |

## Design Principles

- **Evidence over claims** — A finding without a source is an opinion
- **Adversarial over confirmatory** — The Challenger is where research quality comes from
- **Typed over free-form** — Structured claims and scores prevent hand-waving
- **Convergence over completeness** — Stop mining when returns diminish
- **Decision-ready over comprehensive** — NOW/NEXT/NEVER, not "it depends"

## License

MIT
