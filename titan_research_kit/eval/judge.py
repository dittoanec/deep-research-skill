"""
Judge — scores a single item against a rubric using an LLM.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional

from anthropic import Anthropic, APIStatusError

from ..models import JudgeRubric, JudgeResult
from ..prompts.judge import JUDGE_SYSTEM

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0


def judge_item(
    client: Anthropic,
    text: str,
    rubric: JudgeRubric,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 2048,
    context: Optional[str] = None,
) -> JudgeResult:
    """
    Score a single text item against the given rubric.

    Args:
        client: Anthropic API client.
        text: The content to judge.
        rubric: The scoring rubric with named axes.
        model: Model to use for judging.
        max_tokens: Max response tokens.
        context: Optional context (e.g., topic, persona) to include.

    Returns:
        JudgeResult with scores, total, and feedback.
    """
    # Build rubric text for the prompt
    rubric_lines = []
    for axis in rubric.axes:
        rubric_lines.append(
            f"  {axis.name} (weight {axis.weight}x): {axis.description}\n"
            f"    5 = exceptional, 0 = failing"
        )
    rubric_text = "\n".join(rubric_lines)

    system = JUDGE_SYSTEM.format(rubric_text=rubric_text)

    user_msg = f"CONTENT TO JUDGE:\n\n{text}"
    if context:
        user_msg = f"CONTEXT: {context}\n\n{user_msg}"

    # Retry loop for rate limits
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0.1,  # Low temp for consistent scoring
                system=system,
                messages=[{"role": "user", "content": user_msg}],
            )
            break
        except APIStatusError as e:
            if e.status_code == 429 and attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(f"Rate limited, retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Judge API error: {e}")
                return JudgeResult(ok=False)

    raw = response.content[0].text.strip()

    # Parse JSON response
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not json_match:
        logger.warning(f"No JSON in judge response: {raw[:200]}")
        return JudgeResult(ok=False)

    try:
        data = json.loads(json_match.group(0))
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in judge response")
        return JudgeResult(ok=False)

    scores = data.get("scores", {})
    # Ensure all axes are present
    for axis in rubric.axes:
        if axis.name not in scores:
            scores[axis.name] = 0

    total = sum(scores.get(a.name, 0) * a.weight for a in rubric.axes)

    return JudgeResult(
        scores=scores,
        total=total,
        feedback=data.get("feedback", ""),
        ok=True,
    )
