"""
Researcher Agent — conducts structured research passes.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from anthropic import Anthropic

from ...config import AgentConfig
from ...models import (
    Claim,
    ChallengerPassResult,
    Evidence,
    ResearchPassResult,
    Source,
)
from ...prompts.researcher import RESEARCHER_SYSTEM, RESEARCHER_FOLLOWUP

logger = logging.getLogger(__name__)


class ResearcherAgent:
    """Executes a single research pass, producing structured claims."""

    def __init__(self, config: AgentConfig, api_key: str):
        self.config = config
        self.client = Anthropic(api_key=api_key)

    def research(
        self,
        query: str,
        pass_number: int,
        previous_result: Optional[ResearchPassResult] = None,
        challenger_result: Optional[ChallengerPassResult] = None,
    ) -> ResearchPassResult:
        """
        Execute one research pass.

        On pass 1, conduct broad research. On subsequent passes,
        target gaps identified by the Challenger.
        """
        system = RESEARCHER_SYSTEM.format(pass_number=pass_number)

        # Build user message
        if pass_number == 1 or not challenger_result:
            user_msg = f"Research this question thoroughly:\n\n{query}"
        else:
            gaps_text = "\n".join(
                f"- [{g.severity.value.upper()}] {g.description} "
                f"(suggested searches: {', '.join(g.suggested_queries)})"
                for g in (challenger_result.gaps if challenger_result else [])
            )
            contested_text = "\n".join(
                f"- {cid}" for cid in (challenger_result.contested_claims if challenger_result else [])
            )
            followup = RESEARCHER_FOLLOWUP.format(
                pass_number=pass_number,
                gaps=gaps_text or "None",
                contested=contested_text or "None",
            )
            user_msg = f"Original query: {query}\n\n{followup}"

        # Call LLM
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )

        raw_text = response.content[0].text.strip()
        return self._parse_response(raw_text, query, pass_number)

    def _parse_response(
        self, raw: str, query: str, pass_number: int
    ) -> ResearchPassResult:
        """Parse the LLM response into a structured ResearchPassResult."""
        # Try to extract JSON
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            logger.warning("No JSON found in researcher response, using raw text")
            return ResearchPassResult(
                pass_number=pass_number,
                query=query,
                raw_summary=raw,
            )

        try:
            data = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            logger.warning("Failed to parse researcher JSON, using raw text")
            return ResearchPassResult(
                pass_number=pass_number,
                query=query,
                raw_summary=raw,
            )

        # Build claims
        claims = []
        for c in data.get("claims", []):
            evidence_list = []
            for e in c.get("evidence", []):
                src_data = e.get("source", {})
                evidence_list.append(Evidence(
                    content=e.get("content", ""),
                    source=Source(
                        url=src_data.get("url"),
                        title=src_data.get("title", "Unknown"),
                        author=src_data.get("author"),
                        source_type=src_data.get("source_type", "web"),
                    ),
                    quality=e.get("quality", "unverified"),
                    supports_claim=e.get("supports_claim", True),
                ))
            claims.append(Claim(
                id=c.get("id", f"claim_{len(claims)+1:03d}"),
                statement=c.get("statement", ""),
                category=c.get("category", "general"),
                evidence=evidence_list,
                confidence=c.get("confidence", 0.5),
                notes=c.get("notes"),
            ))

        return ResearchPassResult(
            pass_number=pass_number,
            query=query,
            sub_questions=data.get("sub_questions", []),
            claims=claims,
            raw_summary=data.get("raw_summary", ""),
            sources_consulted=data.get("sources_consulted", 0),
        )
