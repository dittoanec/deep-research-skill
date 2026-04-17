---
name: eval-loop
description: "Use when you need to judge, score, and improve a batch of LLM-generated outputs. Signals: evaluate quality, judge these, score outputs, improve bottom quartile, quality gate, regen weak ones."
---

Judge a batch of generated outputs on a configurable rubric, rank them, regenerate the weakest with targeted feedback, and re-judge to measure lift. This is the compound-iteration loop that turns mediocre batches into consistently high-quality ones.

<HARD-GATE>
Do NOT skip the re-judge step after regeneration. The lift measurement is what proves the loop works. Without it, you're just rewriting — not improving.
</HARD-GATE>

## When to Use
- After generating a batch of content (articles, anecdotes, summaries, code)
- After a research pass to quality-gate claims
- Whenever quality variance across outputs is high and you want to raise the floor
- When you need quantitative proof that iteration improved quality

## Process Flow
```
Input Batch → Judge All (parallel) → Rank by Score → Pick Bottom N%
     → Inject Feedback into Regen Prompt → Regenerate → Re-Judge
     → Measure Lift → Report
```

## Phase 1: Define Rubric
Before judging, establish the scoring axes. Each axis has:
- **Name**: What you're measuring (e.g., `accuracy`, `voice_match`, `novelty`)
- **Description**: 1-sentence criteria for what earns a 5 vs a 1
- **Scale**: 0-5 (default) per axis
- **Weight**: Relative importance (default: 1.0 each)

### Built-in Presets

**Content Generation** (`content`):
| Axis | Description |
|------|-------------|
| voice_match | How well does it match the target voice/style? |
| specificity | Concrete details — numbers, names, places, quotes? |
| novelty | Non-obvious angle? No platitudes or familiar templates? |
| emotional_resonance | Does it make the reader pause and feel something? |

**Research Claims** (`research`):
| Axis | Description |
|------|-------------|
| accuracy | Is the claim factually correct and precisely stated? |
| evidence_quality | Is it backed by reliable, cited sources? |
| balance | Are counter-arguments and alternative views represented? |
| actionability | Can someone make a decision based on this? |

**Code Review** (`code`):
| Axis | Description |
|------|-------------|
| correctness | Does it solve the stated problem without bugs? |
| readability | Is it clear, well-named, properly structured? |
| efficiency | Is it performant without premature optimization? |
| robustness | Does it handle edge cases, errors, bad input? |

You can also define a **custom rubric** by specifying axes inline.

## Phase 2: Judge
For each item in the batch, invoke the judge with:

```
You are scoring this [content type] on [N] axes, each 0-5.

RUBRIC:
[axis_name]: [description]
  5 = [what a 5 looks like]
  1 = [what a 1 looks like]

ITEM TO JUDGE:
[the content]

Respond with JSON: {"scores": {"axis1": N, ...}, "total": N, "feedback": "one paragraph of specific, actionable feedback"}
```

### Judge Rules
- Scores MUST be integers 0-5
- Feedback MUST be specific — "add more detail" is useless; "the claim about X lacks a source — cite the WHO 2024 report or similar" is useful
- Judge calls should be parallelized (rate-limit with retry)
- Failed judge calls → skip item, don't block batch

## Phase 3: Rank & Select
1. Sort all scored items by total (ascending)
2. Select bottom N% for regeneration (default: 25%)
3. Log the score distribution: mean, median, min, max per axis

## Phase 4: Regenerate with Feedback
For each item in the bottom N%:

```
The following [content type] scored [X]/[max] on our quality rubric.

ORIGINAL:
[the content]

JUDGE FEEDBACK:
[the feedback from Phase 2]

AXIS BREAKDOWN:
[axis: score for each]

Rewrite this to specifically address the judge's feedback. Focus on the weakest axis ([axis_name]: [score]).
```

### Regen Rules
- The judge feedback is the most important input — it tells the model exactly what's wrong
- Don't rewrite from scratch; improve the original
- Maintain the same topic/intent/framing — only fix the quality issues

## Phase 5: Re-Judge & Measure Lift
1. Run the same judge on all regenerated items
2. Calculate lift: `(new_score - old_score)` per item
3. Report:
   - Items improved: N/M (percentage)
   - Average lift: +X.XX points
   - Per-axis breakdown: which axes improved most

## Phase 6: Report
Output a summary:
```markdown
## Eval Loop Report

**Batch size:** N items
**Judged:** N/N successful
**Average score:** X.XX / [max]

### Score Distribution
| Axis | Mean | Min | Max |
|------|------|-----|-----|
| ...  | ...  | ... | ... |

### Regeneration Results
- Bottom 25%: N items regenerated
- Items improved: N/N (XX%)
- Average lift: +X.XX
- Per-axis lift: [breakdown]
```

## Compound Iteration
For maximum quality, run the eval loop multiple times:
```
Batch → Eval Loop (pass 1) → replace bottom with regens → Eval Loop (pass 2) → ...
```
Diminishing returns after ~3 passes. Stop when average lift < 0.5 per pass.

## Programmatic Invocation
```python
from titan_research_kit.eval import EvalLoop, CONTENT_RUBRIC, RESEARCH_RUBRIC

loop = EvalLoop(rubric=CONTENT_RUBRIC, regen_fraction=0.25)
results = loop.run(items)  # items: list of strings
print(f"Lift: {results.avg_lift}")
```

## Anti-Patterns
| Mistake | Fix |
|---------|-----|
| Vague feedback ("needs improvement") | Feedback must name the specific axis and what's missing |
| Regenerating everything | Only regen bottom N% — top items don't need work |
| Skipping re-judge | Without lift measurement, you can't prove the loop works |
| Running 5+ compound passes | Diminishing returns. 2-3 passes is the sweet spot. |
| Same judge model as generator | Works fine in practice (Claude judging Claude), but cross-model judging reduces bias |
