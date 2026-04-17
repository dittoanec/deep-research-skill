---
name: deep-research
description: "Use when conducting research that requires high confidence, multi-perspective analysis, or decision-ready output. Signals: thorough research, deep dive, compare options, evaluate approaches, decision-ready analysis, evidence-based recommendation."
---

Execute adversarial, multi-pass research using the ARCHITECT → MINER → CHALLENGER → COMPILER pipeline. Produces typed claims with evidence tiers and decision-ready output.

<HARD-GATE>
Do NOT skip any phase. Do NOT skip the Challenger phase because findings "seem solid." Do NOT produce a final report without running all four phases. The Challenger phase is where most research value is created.
</HARD-GATE>

## Anti-Pattern: "I Already Know The Answer"
Every research question goes through all four phases. Even when you're confident in the answer. "Obvious" answers are where unexamined assumptions cause the most damage. The Challenger will either confirm your confidence (good) or surface blind spots (better).

## Process Flow
```
ARCHITECT → MINER (×2-5) → [Converged?] → CHALLENGER → [Critical?] → COMPILER → Report
                ↑ no, more angles ↓               ↑ yes ↓
                └────────────────┘               Flag to user
```

## Phase 1: ARCHITECT
**Purpose:** Decompose before you research. Map the territory.

1. **First Principles:** Break the question into fundamental forces (economic, technical, psychological)
2. **MECE Tree:** Create sub-questions that are Mutually Exclusive, Collectively Exhaustive
3. **Divergence Targets:** What to specifically search for counter-evidence on
4. **Blind Spots:** Domains or perspectives you might be missing

**Output:** Research plan with sub-questions, divergence targets, and blind spots.

## Phase 2: MINER (×2-5 passes)
**Purpose:** Gather TYPED CLAIMS from multiple angles. Not essays — structured findings.

Each pass uses a different angle:
1. **Breadth** — Fundamentals, key concepts, major approaches
2. **Depth + Divergence** — Edge cases, contrarian views, critiques, failure modes
3. **Practicality** — Case studies, benchmarks, production experience
4. (optional) **Alternatives** — Completely different approaches from adjacent domains
5. (optional) **Stress-test** — Hidden costs, maintenance burden, failure modes at scale

### Claim Types
Every finding is tagged:
- `factual` — Verified fact with source
- `constraint` — Hard limitation or boundary condition
- `risk` — Potential failure mode or downside
- `recommendation` — Actionable suggestion
- `estimate` — Quantitative approximation

### Evidence Tiers (weakest → strongest)
- `stated` — Someone claimed it, no evidence
- `web` — Found online, single source
- `documented` — In official docs or multiple sources
- `tested` — Verified through benchmarks or experiments
- `production` — Confirmed in real production environments

### Convergence Check
After each pass (starting from pass 2), check:
- Fewer than 2 new substantive findings? → Converged, move to Challenger
- Major sub-questions still unanswered? → Keep mining
- Surprising finding opened new inquiry? → Keep mining

## Phase 3: CHALLENGER
**Purpose:** ATTACK the findings. Assume the conclusions are WRONG and find out why.

This is a Pre-Mortem Red Team analysis. You are adversarial, not performative.

1. **Conflict Detection:** Find claims that contradict each other
2. **Weakness ID:** Which claims rest on weak evidence (stated/web)?
3. **Bias Scan:** Is evidence skewed toward one conclusion?
4. **Counter-Evidence:** For each major claim, what counter-evidence exists?
5. **Gap Analysis:** What claim types are missing? (all recommendations but no risks?)
6. **Staleness Check:** Any claims relying on data >12 months old in a fast-moving domain?

**Verdict:** `proceed` | `needs-more-research` | `fundamentally-flawed`

If verdict is `fundamentally-flawed`, tell the user before compiling. Don't hide it.

## Phase 4: COMPILER
**Purpose:** Synthesize everything into a decision-ready report.

### Output Schema (STRICT)

```markdown
# [Topic]: Research Report

## 1. Executive BLUF (Bottom Line Up Front)
• **The Alpha:** Single most high-leverage insight
• **Confidence Score:** X/100 — [basis]
• **Primary Risk:** Biggest thing that could make this wrong

## 2. Key Findings
Strongest claims organized by theme. Evidence tier for each.

## 3. Decision Matrix
| Option | Effort (1-10) | Impact (1-10) | The Catch |
|--------|---------------|---------------|-----------|
| ...    | ...           | ...           | ...       |

## 4. Blind Spots & Unresolved Conflicts
• What the research couldn't answer
• Where experts disagree and why

## 5. Next Steps
• **NOW:** Do immediately (high confidence, low effort)
• **NEXT:** Do after NOW steps
• **NEVER:** Evidence against, high risk, low reward

## 6. Sources & Evidence Quality
How many claims are documented+ vs stated/web?
```

### Rules
- Every sentence must reduce uncertainty. NO FLUFF.
- If Challenger found critical conflicts, address them — don't gloss over
- If confidence < 50, say so clearly with reasons
- Cite sources

## Programmatic Invocation
For Nova or standalone use, the Python package provides the same pipeline:
```python
from titan_research_kit.research import ResearchOrchestrator
report = ResearchOrchestrator().run("your question here")
```

## Key Principles
- **Evidence over claims** — A finding without a source is an opinion
- **Adversarial over confirmatory** — The Challenger is where quality comes from
- **Typed over free-form** — Structured claims prevent hand-waving
- **Convergence over completeness** — Stop mining when returns diminish
- **Decision-ready over comprehensive** — NOW/NEXT/NEVER, not "it depends"

## Red Flags — STOP
If you catch yourself:
- Skipping the Challenger because "findings are solid" → STOP. Run it.
- Writing a report without a Decision Matrix → STOP. Add one.
- Producing all recommendations but zero risks → STOP. Run Challenger again.
- Confidence score at 90+ but only stated/web evidence → STOP. Score is inflated.
- Glossing over a conflict the Challenger found → STOP. Address it explicitly.

## Common Mistakes
| Mistake | Fix |
|---------|-----|
| Skipping Architect, jumping into research | Always decompose first. MECE tree catches blind spots. |
| Mining 5+ passes when 2 converged | Check convergence after pass 2. Stop when diminishing returns. |
| Performative Challenger ("looks good!") | Challenger must find at least 1 weakness or explain why evidence is genuinely bulletproof. |
| Confidence score not calibrated | 90+ requires production-tier evidence. 70-89 = documented. Below 70 = warn user. |
| BLUF is a paragraph | BLUF is 3 bullets: Alpha, Confidence, Primary Risk. Period. |

## File Convention
```
research_state/
├── pass_1_research.md
├── pass_1_challenge.md
├── pass_2_research.md
├── pass_2_challenge.md
└── ...
research_output/
├── final_report.md
└── evidence_table.md
```
