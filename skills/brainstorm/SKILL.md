---
name: brainstorm
description: "Use when you need to generate novel, non-obvious angles or framings for a topic before generation. Signals: brainstorm ideas, novel angles, creative framings, expand the idea space, beyond obvious approaches."
---

Generate novel, non-obvious angles for a given domain and set of topics. This skill pushes beyond what RAG or retrieval alone can produce by using structured divergent thinking to unlock framings that wouldn't appear in existing corpora.

<HARD-GATE>
Do NOT produce variations of the same obvious angle. Each angle must be genuinely distinct — different context, different stakes, different perspective. If two angles could be summarized as "the same thing said differently," one must be cut.
</HARD-GATE>

## When to Use
- Before a batch generation pass, to seed the idea space with non-obvious framings
- When RAG retrieval keeps returning the same types of results
- When generated content feels repetitive or predictable
- To "unstick" a topic that keeps producing clichéd output

## Process Flow
```
Domain + Topics → Anti-Cliché Framing → Generate N Angles/Topic
     → Dedup & Distinctness Check → Structured Output
```

## Phase 1: Define the Domain
Specify:
- **Domain**: What kind of content you're generating (e.g., "inspirational anecdotes", "technical blog posts", "research hypotheses")
- **Topics**: A list of topic areas, each with optional metadata:
  - `keywords`: Related concepts
  - `emotional_arc`: The narrative shape (e.g., "struggle → breakthrough")
  - `avoid`: Framings to explicitly avoid

## Phase 2: Anti-Cliché Framing
Before generating, establish what NOT to produce. For each topic:

1. List the **3 most obvious angles** someone would write about this topic
2. These are now **banned** — no angle may resemble them
3. List **5 under-explored contexts** where this topic plays out:
   - Domestic life, friendship, loss, creative work, physical craft
   - Aging, parenting, illness, art, nature, travel, boredom
   - Strangers, ritual, bureaucracy, sports, religion, food

## Phase 3: Generate Angles
For each topic, generate N angles (default: 15). Each angle is:
- **Title**: 3-8 word hook
- **Text**: 120-250 word paragraph that:
  1. Names a specific, counterintuitive truth about the topic
  2. Includes 1-2 concrete details (a quote, a setting, a number, a scenario) that could seed a full piece
  3. Avoids the banned cliché framings from Phase 2
  4. Is distinct from every other angle in the batch

### Diversity Check
After generating, verify:
- No two angles share the same context (e.g., both set in a workplace)
- No two angles make the same core argument
- At least 3 different "worlds" are represented (domestic, professional, creative, physical, philosophical)

## Phase 4: Structure Output
Each angle is saved as:
```markdown
---
source_author: Brainstorm
source_sub: _novel
topic_id: [topic]
angle: "[title]"
kind: novel_angle
---

# [Title]

[Text]
```

## Programmatic Invocation
```python
from titan_research_kit.brainstorm import brainstorm_angles

angles = brainstorm_angles(
    domain="inspirational anecdotes",
    topics={"persistence_grit": {"keywords": [...], "emotional_arc": "..."}},
    per_topic=15,
)
```

## Quality Signals for Good Angles
- **Surprising**: Reader thinks "I never thought about it that way"
- **Concrete**: Has a specific detail that makes it vivid, not abstract
- **Seedable**: A writer could turn this into a full piece without much more input
- **Distinct**: Occupies its own niche in the topic's idea space

## Anti-Patterns
| Mistake | Fix |
|---------|-----|
| All angles from one domain (e.g., all business) | Enforce diversity across domestic/creative/physical/philosophical contexts |
| Abstract philosophy without concrete hooks | Every angle needs at least 1 specific detail |
| Variations on the same insight | Distinctness check: could you summarize two angles identically? If yes, cut one |
| Ignoring the anti-cliché step | The 3 banned obvious angles are what prevent predictable output |
| Too many angles (30+) | Quality drops after ~15-20. Better to do 15 excellent than 30 mediocre |
