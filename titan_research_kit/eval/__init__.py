"""
Eval Loop Engine — Judge, rank, regenerate, measure lift.

Public API:
    from titan_research_kit.eval import EvalLoop, CONTENT_RUBRIC, RESEARCH_RUBRIC
    results = EvalLoop(rubric=CONTENT_RUBRIC).run(items)
"""

from .loop import EvalLoop
from .rubrics import CONTENT_RUBRIC, RESEARCH_RUBRIC, CODE_RUBRIC

__all__ = ["EvalLoop", "CONTENT_RUBRIC", "RESEARCH_RUBRIC", "CODE_RUBRIC"]
