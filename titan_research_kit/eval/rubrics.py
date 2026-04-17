"""Pre-built rubric presets for common eval scenarios."""

from ..models import JudgeAxis, JudgeRubric


# --- Content Generation (anecdotes, articles, social posts) ---
CONTENT_RUBRIC = JudgeRubric(
    name="content",
    axes=[
        JudgeAxis(
            name="voice_match",
            description="How well does it match the target voice/style?",
            weight=1.0,
        ),
        JudgeAxis(
            name="specificity",
            description="Concrete details — numbers, names, places, quotes?",
            weight=1.0,
        ),
        JudgeAxis(
            name="novelty",
            description="Non-obvious angle? No platitudes or familiar templates?",
            weight=1.0,
        ),
        JudgeAxis(
            name="emotional_resonance",
            description="Does it make the reader pause and feel something?",
            weight=1.0,
        ),
    ],
)


# --- Research Claims ---
RESEARCH_RUBRIC = JudgeRubric(
    name="research",
    axes=[
        JudgeAxis(
            name="accuracy",
            description="Is the claim factually correct and precisely stated?",
            weight=1.5,
        ),
        JudgeAxis(
            name="evidence_quality",
            description="Is it backed by reliable, cited sources?",
            weight=1.5,
        ),
        JudgeAxis(
            name="balance",
            description="Are counter-arguments and alternative views represented?",
            weight=1.0,
        ),
        JudgeAxis(
            name="actionability",
            description="Can someone make a decision based on this?",
            weight=1.0,
        ),
    ],
)


# --- Code Review ---
CODE_RUBRIC = JudgeRubric(
    name="code",
    axes=[
        JudgeAxis(
            name="correctness",
            description="Does it solve the stated problem without bugs?",
            weight=1.5,
        ),
        JudgeAxis(
            name="readability",
            description="Is it clear, well-named, properly structured?",
            weight=1.0,
        ),
        JudgeAxis(
            name="efficiency",
            description="Is it performant without premature optimization?",
            weight=1.0,
        ),
        JudgeAxis(
            name="robustness",
            description="Does it handle edge cases, errors, bad input?",
            weight=1.0,
        ),
    ],
)
