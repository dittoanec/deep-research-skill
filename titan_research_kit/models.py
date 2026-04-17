"""
Pydantic data models for structured research, eval, and brainstorm output.

Every agent pass produces structured data (not free-form text) to enable
automated convergence tracking, diff-based gap detection, and machine-readable
evidence tables.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EvidenceQuality(str, Enum):
    """Quality tier for a piece of evidence."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


class EvidenceTier(str, Enum):
    """Evidence tier from weakest to strongest (used in skill definitions)."""
    STATED = "stated"
    WEB = "web"
    DOCUMENTED = "documented"
    TESTED = "tested"
    PRODUCTION = "production"


class ClaimType(str, Enum):
    """Type tag for a claim."""
    FACTUAL = "factual"
    CONSTRAINT = "constraint"
    RISK = "risk"
    RECOMMENDATION = "recommendation"
    ESTIMATE = "estimate"


class ClaimStatus(str, Enum):
    """Status of a claim after challenger review."""
    SUPPORTED = "supported"
    CONTESTED = "contested"
    REFUTED = "refuted"
    UNVERIFIED = "unverified"
    NUANCED = "nuanced"


class GapSeverity(str, Enum):
    """How critical a gap is to the research quality."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


# ---------------------------------------------------------------------------
# Research Models
# ---------------------------------------------------------------------------

class Source(BaseModel):
    """A reference source for evidence."""
    url: Optional[str] = None
    title: str
    author: Optional[str] = None
    published_date: Optional[str] = None
    source_type: str = "web"
    reliability_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="0.0 = unreliable, 1.0 = gold standard"
    )


class Evidence(BaseModel):
    """A piece of evidence supporting or contradicting a claim."""
    content: str = Field(description="The evidence text/quote")
    source: Source
    quality: EvidenceQuality = EvidenceQuality.UNVERIFIED
    tier: EvidenceTier = EvidenceTier.WEB
    supports_claim: bool = True
    extracted_at: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )


class Claim(BaseModel):
    """A factual claim extracted from research."""
    id: str = Field(description="Unique identifier, e.g. 'claim_001'")
    statement: str = Field(description="The claim as a clear, falsifiable statement")
    category: str = Field(default="general", description="Topic category")
    claim_type: ClaimType = ClaimType.FACTUAL
    evidence: list[Evidence] = Field(default_factory=list)
    status: ClaimStatus = ClaimStatus.UNVERIFIED
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Confidence in this claim's accuracy"
    )
    notes: Optional[str] = None


class Gap(BaseModel):
    """A gap or weakness identified by the Challenger agent."""
    id: str = Field(description="Unique identifier, e.g. 'gap_001'")
    description: str = Field(description="What is missing or weak")
    severity: GapSeverity
    affected_claims: list[str] = Field(
        default_factory=list,
        description="IDs of claims affected by this gap"
    )
    suggested_queries: list[str] = Field(
        default_factory=list,
        description="Search queries to address this gap"
    )
    resolved: bool = False
    resolution_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Pass-level Models
# ---------------------------------------------------------------------------

class ResearchPassResult(BaseModel):
    """Output of one Researcher agent pass."""
    pass_number: int
    query: str = Field(description="The research query for this pass")
    sub_questions: list[str] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    raw_summary: str = ""
    sources_consulted: int = 0
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )


class ChallengerPassResult(BaseModel):
    """Output of one Challenger agent pass."""
    pass_number: int
    gaps: list[Gap] = Field(default_factory=list)
    contested_claims: list[str] = Field(default_factory=list)
    bias_detected: list[str] = Field(default_factory=list)
    overall_assessment: str = ""
    convergence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )


# ---------------------------------------------------------------------------
# Research State & Final Report
# ---------------------------------------------------------------------------

class ConvergenceMetrics(BaseModel):
    """Tracks convergence across passes."""
    total_passes: int = 0
    new_gaps_per_pass: list[int] = Field(default_factory=list)
    convergence_scores: list[float] = Field(default_factory=list)
    is_converged: bool = False
    convergence_reason: Optional[str] = None


class ResearchState(BaseModel):
    """Shared state across all passes — CORAL-inspired shared memory."""
    query: str
    research_passes: list[ResearchPassResult] = Field(default_factory=list)
    challenger_passes: list[ChallengerPassResult] = Field(default_factory=list)
    all_claims: list[Claim] = Field(default_factory=list)
    all_gaps: list[Gap] = Field(default_factory=list)
    convergence: ConvergenceMetrics = Field(default_factory=ConvergenceMetrics)
    started_at: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    completed_at: Optional[str] = None


class FinalReport(BaseModel):
    """The compiled final research report."""
    title: str
    query: str
    executive_summary: str
    key_findings: list[str] = Field(default_factory=list)
    detailed_analysis: str = ""
    evidence_table: list[Claim] = Field(default_factory=list)
    dissenting_views: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence_rating: float = Field(default=0.5, ge=0.0, le=1.0)
    total_passes: int = 0
    total_sources: int = 0
    methodology_notes: str = ""
    generated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )


# ---------------------------------------------------------------------------
# Eval Loop Models
# ---------------------------------------------------------------------------

class JudgeAxis(BaseModel):
    """A single scoring axis in a judge rubric."""
    name: str
    description: str
    weight: float = 1.0


class JudgeRubric(BaseModel):
    """A configurable judge rubric with named axes."""
    name: str
    axes: list[JudgeAxis]
    scale: tuple[int, int] = (0, 5)

    @property
    def max_total(self) -> float:
        return self.scale[1] * len(self.axes)


class JudgeResult(BaseModel):
    """Result of judging a single item."""
    scores: dict[str, int] = Field(default_factory=dict)
    total: float = 0.0
    feedback: str = ""
    ok: bool = True


class EvalItem(BaseModel):
    """A single item in an eval batch."""
    id: str = ""
    text: str
    metadata: dict = Field(default_factory=dict)
    judge_result: Optional[JudgeResult] = None
    regen_text: Optional[str] = None
    regen_result: Optional[JudgeResult] = None

    @property
    def lift(self) -> Optional[float]:
        if self.judge_result and self.regen_result:
            return self.regen_result.total - self.judge_result.total
        return None


class EvalReport(BaseModel):
    """Summary report from an eval loop run."""
    batch_size: int
    judged_count: int
    avg_score: float
    per_axis_avg: dict[str, float] = Field(default_factory=dict)
    regen_count: int = 0
    improved_count: int = 0
    avg_lift: float = 0.0
    per_axis_lift: dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Brainstorm Models
# ---------------------------------------------------------------------------

class BrainstormAngle(BaseModel):
    """A single brainstormed angle."""
    title: str
    text: str
    topic_id: str = ""
    domain: str = ""


class BrainstormResult(BaseModel):
    """Result of brainstorming for one topic."""
    topic_id: str
    domain: str
    angles: list[BrainstormAngle] = Field(default_factory=list)
    banned_cliches: list[str] = Field(default_factory=list)
