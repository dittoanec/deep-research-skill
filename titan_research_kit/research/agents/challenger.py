"""
Challenger Agent — adversarial review of research findings.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from anthropic import Anthropic

from ...config import AgentConfig
from ...models import (
    ChallengerPassResult,
    Gap,
    GapSeverity,
    ResearchPassResult,
    ResearchState,
)
from ...prompts.challenger import CHALLENGER_SYSTEM

logger = logging.getLogger(__name__)


class ChallengerAgent:
    """Reviews research findings adversarially, identifying gaps and bias."""

    def __init__(self, config: AgentConfig, api_key: str):
        self.config = config
        self.client = Anthropic(api_key=api_key)

    def challenge(
        self,
        query: str,
        research_result: ResearchPassResult,
        state: ResearchState,
        pass_number: int,
    ) -> ChallengerPassResult:
        """Execute one challenger review pass."""
        system = CHALLENGER_SYSTEM.format(pass_number=pass_number)

        # Build context for challenger
        claims_text = "\n".join(
            f"  {c.id}: [{c.claim_type.value}] {c.statement} "
            f"(confidence: {c.confidence:.0%}, evidence: {len(c.evidence)} sources)"
            for c in research_result.claims
        )

        user_msg = (
            f"RESEARCH QUERY: {query}\n\n"
            f"CLAIMS FROM PASS {pass_number}:\n{claims_text}\n\n"
            f"SUMMARY:\n{research_result.raw_summary}\n\n"
            f"TOTAL CLAIMS ACROSS ALL PASSES: {len(state.all_claims)}\n"
            f"EXISTING GAPS: {len(state.all_gaps)}\n\n"
            f"Review these findings. Find weaknesses, gaps, bias, and counter-evidence."
        )

        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )

        raw_text = response.content[0].text.strip()
        return self._parse_response(raw_text, pass_number)

    def _parse_response(
        self, raw: str, pass_number: int
    ) -> ChallengerPassResult:
        """Parse the LLM response into a structured ChallengerPassResult."""
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            logger.warning("No JSON found in challenger response")
            return ChallengerPassResult(
                pass_number=pass_number,
                overall_assessment=raw,
                convergence_score=0.3,
            )

        try:
            data = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            logger.warning("Failed to parse challenger JSON")
            return ChallengerPassResult(
                pass_number=pass_number,
                overall_assessment=raw,
                convergence_score=0.3,
            )

        # Build gaps
        gaps = []
        for g in data.get("gaps", []):
            severity_str = g.get("severity", "minor").lower()
            try:
                severity = GapSeverity(severity_str)
            except ValueError:
                severity = GapSeverity.MINOR

            gaps.append(Gap(
                id=g.get("id", f"gap_{len(gaps)+1:03d}"),
                description=g.get("description", ""),
                severity=severity,
                affected_claims=g.get("affected_claims", []),
                suggested_queries=g.get("suggested_queries", []),
            ))

        return ChallengerPassResult(
            pass_number=pass_number,
            gaps=gaps,
            contested_claims=data.get("contested_claims", []),
            bias_detected=data.get("bias_detected", []),
            overall_assessment=data.get("overall_assessment", ""),
            convergence_score=data.get("convergence_score", 0.5),
        )
