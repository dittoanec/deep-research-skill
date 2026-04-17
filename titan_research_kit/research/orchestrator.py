"""
Research Orchestrator — Multi-pass loop controller.

Implements: ARCHITECT → MINER → CHALLENGER → (converge?) → COMPILER
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..config import ResearchConfig, TitanConfig
from ..models import (
    ConvergenceMetrics,
    FinalReport,
    ResearchState,
)
from .agents import ResearcherAgent, ChallengerAgent, CompilerAgent

logger = logging.getLogger(__name__)
console = Console()


class ResearchOrchestrator:
    """
    Orchestrates the multi-pass research pipeline.

    The loop:
        1. Researcher generates findings (Pass N)
        2. Challenger reviews and identifies gaps
        3. Check convergence — if converged, go to step 5
        4. Go back to step 1 with gap-targeted query
        5. Compiler synthesizes final report
    """

    def __init__(
        self,
        config: Optional[TitanConfig] = None,
        research_config: Optional[ResearchConfig] = None,
    ):
        cfg = config or TitanConfig()
        rcfg = research_config or cfg.research
        api_key = cfg.anthropic_api_key

        # Validate
        errors = cfg.validate()
        if errors:
            for error in errors:
                console.print(f"[red]❌ Config error: {error}[/red]")
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

        self.config = rcfg
        self.api_key = api_key

        # Initialize agents
        self.researcher = ResearcherAgent(
            config=rcfg.researcher,
            api_key=api_key,
        )
        self.challenger = ChallengerAgent(
            config=rcfg.challenger,
            api_key=api_key,
        )
        self.compiler = CompilerAgent(
            config=rcfg.compiler,
            api_key=api_key,
        )

    def run(self, query: str) -> FinalReport:
        """Execute the full multi-pass research pipeline."""
        console.print(Panel(
            f"[bold cyan]🔬 Titan Deep Research[/bold cyan]\n\n"
            f"[white]Query:[/white] {query}\n"
            f"[dim]Max passes: {self.config.max_passes} | "
            f"Convergence threshold: {self.config.convergence_threshold}[/dim]",
            border_style="cyan",
        ))

        state = ResearchState(query=query)

        # --- Multi-Pass Loop ---
        for pass_num in range(1, self.config.max_passes + 1):
            console.rule(f"[bold yellow]Pass {pass_num} of {self.config.max_passes}[/bold yellow]")

            # Step 1: Research
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"🔬 Researcher Agent (Pass {pass_num})...", total=None
                )
                prev_research = (
                    state.research_passes[-1] if state.research_passes else None
                )
                prev_challenge = (
                    state.challenger_passes[-1] if state.challenger_passes else None
                )
                research_result = self.researcher.research(
                    query=query,
                    pass_number=pass_num,
                    previous_result=prev_research,
                    challenger_result=prev_challenge,
                )
                progress.update(task, completed=True)

            # Merge claims
            self._merge_claims(state, research_result)
            state.research_passes.append(research_result)
            self._display_research_summary(research_result)

            if self.config.save_intermediate:
                self._save_state(state)

            # Step 2: Challenger
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"⚔️  Challenger Agent (Review {pass_num})...", total=None
                )
                challenger_result = self.challenger.challenge(
                    query=query,
                    research_result=research_result,
                    state=state,
                    pass_number=pass_num,
                )
                progress.update(task, completed=True)

            self._merge_gaps(state, challenger_result)
            state.challenger_passes.append(challenger_result)
            self._update_convergence(state, challenger_result)
            self._display_challenger_summary(challenger_result)

            if self.config.save_intermediate:
                self._save_state(state)

            # Step 3: Convergence check
            if self._check_convergence(state, pass_num):
                console.print(
                    f"\n[bold green]✅ Converged after {pass_num} passes![/bold green]"
                )
                break

            # Human-in-the-loop checkpoint
            if self.config.pause_after_first_challenge and pass_num == 1:
                console.print(
                    "\n[bold yellow]⏸  Paused for human review.[/bold yellow]"
                )
                console.print(
                    "[dim]Review gaps above. Press Enter to continue or Ctrl+C to abort.[/dim]"
                )
                try:
                    input()
                except KeyboardInterrupt:
                    console.print("\n[red]Aborted by user.[/red]")
                    state.completed_at = datetime.now().isoformat()
                    self._save_state(state)
                    raise

        # --- Step 4: Compile ---
        console.rule("[bold green]Compiling Final Report[/bold green]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("📝 Compiler Agent...", total=None)
            report = self.compiler.compile(state)
            progress.update(task, completed=True)

        state.completed_at = datetime.now().isoformat()
        self._save_state(state)
        self._save_report(report)
        self._display_report_summary(report)

        return report

    # ------------------------------------------------------------------
    # State Management
    # ------------------------------------------------------------------

    def _merge_claims(self, state, research_result):
        existing_ids = {c.id for c in state.all_claims}
        for claim in research_result.claims:
            if claim.id not in existing_ids:
                state.all_claims.append(claim)
                existing_ids.add(claim.id)
            else:
                for existing in state.all_claims:
                    if existing.id == claim.id:
                        existing.evidence.extend(claim.evidence)
                        existing.confidence = max(existing.confidence, claim.confidence)
                        break

    def _merge_gaps(self, state, challenger_result):
        existing_ids = {g.id for g in state.all_gaps}
        for gap in challenger_result.gaps:
            if gap.id not in existing_ids:
                state.all_gaps.append(gap)

    def _update_convergence(self, state, challenger_result):
        metrics = state.convergence
        metrics.total_passes += 1
        metrics.new_gaps_per_pass.append(len(challenger_result.gaps))
        metrics.convergence_scores.append(challenger_result.convergence_score)

    def _check_convergence(self, state, pass_num):
        metrics = state.convergence
        if pass_num < self.config.min_passes:
            return False
        if metrics.convergence_scores:
            if metrics.convergence_scores[-1] >= self.config.convergence_threshold:
                metrics.is_converged = True
                metrics.convergence_reason = (
                    f"Score {metrics.convergence_scores[-1]:.2f} >= "
                    f"threshold {self.config.convergence_threshold}"
                )
                return True
        if metrics.new_gaps_per_pass:
            if metrics.new_gaps_per_pass[-1] <= self.config.max_new_gaps_to_converge:
                metrics.is_converged = True
                metrics.convergence_reason = (
                    f"Only {metrics.new_gaps_per_pass[-1]} new gaps "
                    f"(<= {self.config.max_new_gaps_to_converge})"
                )
                return True
        return False

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_state(self, state):
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        state_file = output_dir / "research_state.json"
        state_file.write_text(state.model_dump_json(indent=2), encoding="utf-8")

    def _save_report(self, report):
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        json_file = output_dir / "final_report.json"
        json_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        md_file = output_dir / "final_report.md"
        md_file.write_text(report.detailed_analysis, encoding="utf-8")

        console.print(f"\n[dim]📁 Report saved to {output_dir}/[/dim]")

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _display_research_summary(self, result):
        table = Table(title=f"Research Pass {result.pass_number}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Claims found", str(len(result.claims)))
        table.add_row("Sources consulted", str(result.sources_consulted))
        table.add_row("Sub-questions", str(len(result.sub_questions)))
        console.print(table)

        if result.claims:
            console.print("\n[bold]Top Claims:[/bold]")
            for claim in result.claims[:5]:
                color = (
                    "green" if claim.confidence >= 0.7
                    else "yellow" if claim.confidence >= 0.4
                    else "red"
                )
                console.print(
                    f"  [{color}]●[/{color}] {claim.statement[:100]}  "
                    f"[dim](conf: {claim.confidence:.0%})[/dim]"
                )

    def _display_challenger_summary(self, result):
        score = result.convergence_score
        color = (
            "green" if score >= 0.8
            else "yellow" if score >= 0.5
            else "red"
        )
        console.print(Panel(
            f"[bold]Convergence:[/bold] [{color}]{score:.0%}[/{color}]\n"
            f"[bold]Gaps:[/bold] {len(result.gaps)}\n"
            f"[bold]Contested:[/bold] {len(result.contested_claims)}\n"
            f"[bold]Bias:[/bold] {', '.join(result.bias_detected[:3]) or 'None'}",
            title=f"⚔️ Challenger Review {result.pass_number}",
            border_style=color,
        ))

    def _display_report_summary(self, report):
        console.print(Panel(
            f"[bold]{report.title}[/bold]\n\n"
            f"{report.executive_summary[:500]}\n\n"
            f"[dim]Confidence: {report.confidence_rating:.0%} | "
            f"Sources: {report.total_sources} | "
            f"Passes: {report.total_passes}[/dim]",
            title="📋 Final Report",
            border_style="green",
        ))
