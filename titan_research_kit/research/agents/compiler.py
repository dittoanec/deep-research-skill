"""
Compiler Agent — synthesizes multi-pass research into a final report.
"""

from __future__ import annotations

import json
import logging
import re

from anthropic import Anthropic

from ...config import AgentConfig
from ...models import FinalReport, ResearchState
from ...prompts.compiler import COMPILER_SYSTEM

logger = logging.getLogger(__name__)


class CompilerAgent:
    """Compiles all research and challenger passes into a final report."""

    def __init__(self, config: AgentConfig, api_key: str):
        self.config = config
        self.client = Anthropic(api_key=api_key)

    def compile(self, state: ResearchState) -> FinalReport:
        """Compile all passes into a final report."""
        # Build system with state metadata
        convergence = (
            state.convergence.convergence_scores[-1]
            if state.convergence.convergence_scores
            else 0.0
        )
        system = COMPILER_SYSTEM.format(
            num_research_passes=len(state.research_passes),
            num_challenger_passes=len(state.challenger_passes),
            convergence_score=f"{convergence:.2f}",
        )

        # Build comprehensive context
        sections = [f"ORIGINAL QUERY: {state.query}\n"]

        for rp in state.research_passes:
            sections.append(f"--- RESEARCH PASS {rp.pass_number} ---")
            sections.append(f"Sub-questions: {', '.join(rp.sub_questions)}")
            for c in rp.claims:
                evidence_count = len(c.evidence)
                sections.append(
                    f"  {c.id} [{c.claim_type.value}]: {c.statement} "
                    f"(conf: {c.confidence:.0%}, evidence: {evidence_count})"
                )
            sections.append(f"Summary: {rp.raw_summary}\n")

        for cp in state.challenger_passes:
            sections.append(f"--- CHALLENGER REVIEW {cp.pass_number} ---")
            sections.append(f"Convergence: {cp.convergence_score:.2f}")
            for g in cp.gaps:
                sections.append(
                    f"  [{g.severity.value.upper()}] {g.description}"
                )
            if cp.bias_detected:
                sections.append(f"Bias: {', '.join(cp.bias_detected)}")
            sections.append(f"Assessment: {cp.overall_assessment}\n")

        user_msg = "\n".join(sections)
        user_msg += (
            "\n\nCompile these findings into a decision-ready report "
            "following the STRICT output format in your instructions."
        )

        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )

        raw_text = response.content[0].text.strip()
        return self._build_report(raw_text, state, convergence)

    def _build_report(
        self, markdown: str, state: ResearchState, convergence: float
    ) -> FinalReport:
        """Build a FinalReport from the compiler's markdown output."""
        # Extract title from first heading
        title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
        title = title_match.group(1) if title_match else "Research Report"

        # Extract executive summary / BLUF
        bluf_match = re.search(
            r"##\s+1\.\s+Executive.*?\n(.*?)(?=\n##\s+2\.|\Z)",
            markdown,
            re.DOTALL,
        )
        executive = bluf_match.group(1).strip() if bluf_match else ""

        # Extract key findings
        findings_match = re.search(
            r"##\s+2\.\s+Key Findings\n(.*?)(?=\n##\s+3\.|\Z)",
            markdown,
            re.DOTALL,
        )
        findings_text = findings_match.group(1).strip() if findings_match else ""
        key_findings = [
            line.strip().lstrip("0123456789.-) ")
            for line in findings_text.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]

        # Count total sources
        total_sources = sum(
            len(c.evidence) for c in state.all_claims
        )

        # Extract limitations
        lim_match = re.search(
            r"(?:Limitations|Blind Spots).*?\n(.*?)(?=\n##|\Z)",
            markdown,
            re.DOTALL,
        )
        limitations = []
        if lim_match:
            limitations = [
                line.strip().lstrip("•-* ")
                for line in lim_match.group(1).split("\n")
                if line.strip() and line.strip()[0] in "•-*"
            ]

        return FinalReport(
            title=title,
            query=state.query,
            executive_summary=executive,
            key_findings=key_findings,
            detailed_analysis=markdown,
            evidence_table=state.all_claims,
            dissenting_views=[],
            limitations=limitations,
            confidence_rating=min(convergence, 0.95),
            total_passes=len(state.research_passes),
            total_sources=total_sources,
            methodology_notes=(
                f"Generated through {len(state.research_passes)} research passes "
                f"with {len(state.challenger_passes)} adversarial reviews. "
                f"Final convergence score: {convergence:.2f}."
            ),
        )
