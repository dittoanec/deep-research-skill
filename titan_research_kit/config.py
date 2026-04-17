"""
Unified configuration for the Titan Research Kit.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentConfig:
    """Configuration for a single LLM agent."""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192
    temperature: float = 0.3


@dataclass
class ResearchConfig:
    """Configuration for the deep research pipeline."""

    # --- Models ---
    researcher: AgentConfig = field(default_factory=lambda: AgentConfig(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        temperature=0.2,
    ))
    challenger: AgentConfig = field(default_factory=lambda: AgentConfig(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        temperature=0.4,
    ))
    compiler: AgentConfig = field(default_factory=lambda: AgentConfig(
        model="claude-sonnet-4-20250514",
        max_tokens=16384,
        temperature=0.2,
    ))

    # --- Multi-Pass Loop ---
    max_passes: int = 3
    min_passes: int = 1
    convergence_threshold: float = 0.8
    max_new_gaps_to_converge: int = 2

    # --- Evidence Governance ---
    min_sources_per_claim: int = 1
    recency_weight: float = 0.3

    # --- Output ---
    output_dir: Path = field(
        default_factory=lambda: Path("./research_output")
    )
    save_intermediate: bool = True

    # --- Human-in-the-Loop ---
    pause_after_first_challenge: bool = False


@dataclass
class EvalConfig:
    """Configuration for the eval loop pipeline."""

    # --- Models ---
    judge_model: str = "claude-sonnet-4-20250514"
    regen_model: str = "claude-sonnet-4-20250514"
    judge_max_tokens: int = 2048
    regen_max_tokens: int = 4096

    # --- Eval Loop ---
    regen_fraction: float = 0.25
    max_compound_passes: int = 3
    min_lift_to_continue: float = 0.5

    # --- Parallelism ---
    max_workers: int = 4

    # --- Output ---
    output_dir: Path = field(
        default_factory=lambda: Path("./eval_output")
    )


@dataclass
class BrainstormConfig:
    """Configuration for the brainstorm pipeline."""

    # --- Model ---
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 6000
    temperature: float = 0.7  # Higher for creative divergence

    # --- Generation ---
    per_topic: int = 15
    min_word_count: int = 120
    max_word_count: int = 250

    # --- Output ---
    output_dir: Path = field(
        default_factory=lambda: Path("./brainstorm_output")
    )


@dataclass
class TitanConfig:
    """Top-level configuration for the entire toolkit."""

    # --- API ---
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )

    # --- Sub-configs ---
    research: ResearchConfig = field(default_factory=ResearchConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)
    brainstorm: BrainstormConfig = field(default_factory=BrainstormConfig)

    def validate(self) -> list[str]:
        """Return a list of validation errors, empty if config is valid."""
        errors = []
        if not self.anthropic_api_key:
            errors.append(
                "ANTHROPIC_API_KEY not set. Set it in .env or environment."
            )
        if self.research.max_passes < 1:
            errors.append("research.max_passes must be >= 1")
        if not (0 < self.eval.regen_fraction <= 1):
            errors.append("eval.regen_fraction must be between 0 and 1")
        return errors


def load_config(**overrides) -> TitanConfig:
    """Load configuration with optional overrides."""
    return TitanConfig(**overrides)
