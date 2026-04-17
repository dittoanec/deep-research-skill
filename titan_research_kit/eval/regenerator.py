"""
Regenerator — rewrites content using judge feedback.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from anthropic import Anthropic, APIStatusError

from ..models import JudgeRubric, JudgeResult
from ..prompts.judge import REGEN_SYSTEM

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0


def regenerate_item(
    client: Anthropic,
    original_text: str,
    judge_result: JudgeResult,
    rubric: JudgeRubric,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    context: Optional[str] = None,
) -> str:
    """
    Regenerate content using judge feedback to fix weaknesses.

    Args:
        client: Anthropic API client.
        original_text: The original content that was judged.
        judge_result: The judge's scores and feedback.
        rubric: The scoring rubric (for axis names and scale).
        model: Model to use for regeneration.
        max_tokens: Max response tokens.
        context: Optional context to include.

    Returns:
        The regenerated text.
    """
    # Find weakest axis
    weakest_axis = min(
        judge_result.scores,
        key=lambda k: judge_result.scores[k],
    )
    weakest_score = judge_result.scores[weakest_axis]

    # Build axis breakdown
    axis_lines = [
        f"  {name}: {score}/{rubric.scale[1]}"
        for name, score in judge_result.scores.items()
    ]
    axis_breakdown = "\n".join(axis_lines)

    system = REGEN_SYSTEM.format(
        score=judge_result.total,
        max_score=rubric.max_total,
        original=original_text,
        feedback=judge_result.feedback,
        axis_breakdown=axis_breakdown,
        weakest_axis=weakest_axis,
        weakest_score=weakest_score,
        scale_max=rubric.scale[1],
    )

    user_msg = "Rewrite the content following the instructions above."
    if context:
        user_msg = f"CONTEXT: {context}\n\n{user_msg}"

    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0.4,
                system=system,
                messages=[{"role": "user", "content": user_msg}],
            )
            return response.content[0].text.strip()
        except APIStatusError as e:
            if e.status_code == 429 and attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(f"Rate limited, retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Regen API error: {e}")
                return original_text  # Fall back to original

    return original_text
