# 🔬 Titan Research Kit

An agentic research skill set that goes beyond single-pass research. Three capabilities — deep research, eval loop, and brainstorm — in one plugin.

Most research skills stop at "search → summarize." This one adds adversarial validation (hard-gated Challenger that can't be skipped), configurable eval loops (judge → regen → measure lift), and structured brainstorming with anti-cliché guards.

## What It Does

1. **Deep Research** — Multi-pass ARCHITECT → MINER → CHALLENGER → COMPILER pipeline. Typed claims, evidence tiers, adversarial review. Output: decision-ready BLUF report.

2. **Eval Loop** — Judge a batch of outputs on a configurable rubric, regenerate the bottom 25% with feedback injection, re-judge to measure lift. Proves improvement quantitatively.

3. **Brainstorm** — Generate novel angles for any topic. Bans the 3 most obvious framings before generating, enforces diversity across life contexts.

## Installation

### Per-Project (recommended)

Clone and copy the skills into your project's `.claude/skills/` directory:

```bash
git clone https://github.com/dittoanec/deep-research-skill.git /tmp/titan-research-kit
cp -r /tmp/titan-research-kit/skills/ .claude/skills/
```

That's it. Claude Code auto-detects skills in `.claude/skills/` — no restart needed.

### Global (all projects)

```bash
git clone https://github.com/dittoanec/deep-research-skill.git ~/.titan-research-kit
mkdir -p ~/.claude/skills
ln -sf ~/.titan-research-kit/skills/deep-research ~/.claude/skills/deep-research
ln -sf ~/.titan-research-kit/skills/eval-loop ~/.claude/skills/eval-loop
ln -sf ~/.titan-research-kit/skills/brainstorm ~/.claude/skills/brainstorm
```

### Python Package (for programmatic use)

```bash
git clone https://github.com/dittoanec/deep-research-skill.git titan-research-kit
cd titan-research-kit
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

Once installed, just ask naturally. The skills trigger automatically:

- *"Do deep research on X"* → runs the full 4-phase pipeline
- *"Judge these outputs"* → runs eval loop with content rubric
- *"Brainstorm angles for Y"* → generates novel angles

### Python API

```python
from titan_research_kit.research import ResearchOrchestrator
from titan_research_kit.eval import EvalLoop, CONTENT_RUBRIC
from titan_research_kit.brainstorm import brainstorm_angles

# Deep research
report = ResearchOrchestrator().run("What is the best approach to X?")

# Eval loop
results = EvalLoop(rubric=CONTENT_RUBRIC).run(["item 1", "item 2", ...])

# Brainstorm
angles = brainstorm_angles(domain="blog posts", topics={"ai": {"keywords": ["ethics"]}})
```

### CLI

```bash
python -m titan_research_kit research "What is the best database for time-series data?"
python -m titan_research_kit eval --input outputs.txt --rubric content
python -m titan_research_kit brainstorm --domain "content" --topics ai,leadership
```

## Rubric Presets

| Preset | Axes | Best For |
|--------|------|----------|
| `content` | voice_match, specificity, novelty, emotional_resonance | Articles, anecdotes, social posts |
| `research` | accuracy, evidence_quality, balance, actionability | Research claims, analysis |
| `code` | correctness, readability, efficiency, robustness | Code review, generated code |

Custom rubrics are also supported — see `titan_research_kit/eval/rubrics.py`.

## How It's Different

| | Typical research skills | Titan Research Kit |
|-|-------------------------|-------------------|
| **Scope** | Research only | Research + eval loop + brainstorm |
| **Adversarial review** | Optional or performative | Hard-gated — Challenger can't be skipped |
| **Evidence** | Free-form summaries | Typed claims with 5-tier evidence governance |
| **Quality loop** | ❌ | Judge → regen → re-judge with measured lift |
| **Brainstorm** | ❌ | Anti-cliché guards + diversity enforcement |
| **Integration** | Skill-only or code-only | Both: Claude CLI skills + Python package |

## Design Principles

- **Evidence over claims** — A finding without a source is an opinion
- **Adversarial over confirmatory** — The Challenger is where quality comes from
- **Typed over free-form** — Structured claims and scores prevent hand-waving
- **Convergence over completeness** — Stop mining when returns diminish
- **Decision-ready over comprehensive** — NOW/NEXT/NEVER, not "it depends"

## License

MIT
