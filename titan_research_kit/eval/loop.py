"""
Eval Loop — Judge → Rank → Regen bottom N% → Re-judge → Report.
"""

from __future__ import annotations

import concurrent.futures as cf
import logging
import time
from typing import Optional

from anthropic import Anthropic
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..config import EvalConfig, TitanConfig
from ..models import EvalItem, EvalReport, JudgeRubric, JudgeResult
from .judge import judge_item
from .regenerator import regenerate_item

logger = logging.getLogger(__name__)
console = Console()


class EvalLoop:
    """
    Orchestrates the judge-rank-regen-rejudge loop.

    Usage:
        loop = EvalLoop(rubric=CONTENT_RUBRIC)
        report = loop.run(items)
    """

    def __init__(
        self,
        rubric: JudgeRubric,
        config: Optional[TitanConfig] = None,
        eval_config: Optional[EvalConfig] = None,
    ):
        cfg = config or TitanConfig()
        self.eval_cfg = eval_config or cfg.eval
        self.rubric = rubric
        self.client = Anthropic(api_key=cfg.anthropic_api_key)

    def run(
        self,
        items: list[str] | list[EvalItem],
        regen_fraction: Optional[float] = None,
        context: Optional[str] = None,
    ) -> EvalReport:
        """
        Run the full eval loop on a batch of items.

        Args:
            items: List of text strings or EvalItem objects.
            regen_fraction: Override the config's regen fraction.
            context: Optional context string passed to judge/regen.

        Returns:
            EvalReport with scores, lift metrics, and per-axis breakdowns.
        """
        frac = regen_fraction or self.eval_cfg.regen_fraction

        # Normalize to EvalItem
        eval_items = []
        for i, item in enumerate(items):
            if isinstance(item, str):
                eval_items.append(EvalItem(id=f"item_{i:03d}", text=item))
            else:
                eval_items.append(item)

        console.print(Panel(
            f"[bold cyan]📊 Eval Loop[/bold cyan]\n\n"
            f"Rubric: {self.rubric.name} ({len(self.rubric.axes)} axes)\n"
            f"Items: {len(eval_items)}\n"
            f"Regen fraction: {frac:.0%}",
            border_style="cyan",
        ))

        # Phase 1: Judge all
        console.print("\n[bold]Phase 1: Judging...[/bold]")
        t0 = time.time()
        self._judge_batch(eval_items, context)
        dt = time.time() - t0

        scored = [it for it in eval_items if it.judge_result and it.judge_result.ok]
        console.print(
            f"  Judged {len(scored)}/{len(eval_items)} in {dt:.0f}s"
        )

        if not scored:
            console.print("[red]No items were successfully judged.[/red]")
            return EvalReport(
                batch_size=len(eval_items),
                judged_count=0,
                avg_score=0.0,
            )

        # Phase 2: Rank & select bottom N%
        scored.sort(key=lambda it: it.judge_result.total)
        cutoff = max(1, int(len(scored) * frac))
        bottom = scored[:cutoff]

        avg_score = sum(it.judge_result.total for it in scored) / len(scored)
        per_axis_avg = self._per_axis_avg(scored)

        self._display_scores(scored, per_axis_avg, avg_score)

        # Phase 3: Regenerate bottom N%
        console.print(f"\n[bold]Phase 3: Regenerating bottom {cutoff}...[/bold]")
        self._regen_batch(bottom, context)

        # Phase 4: Re-judge regens
        console.print("[bold]Phase 4: Re-judging regens...[/bold]")
        self._rejudge_batch(bottom, context)

        # Phase 5: Measure lift
        improved = [it for it in bottom if it.lift and it.lift > 0]
        avg_lift = (
            sum(it.lift for it in bottom if it.lift is not None) / len(bottom)
            if bottom
            else 0.0
        )
        per_axis_lift = self._per_axis_lift(bottom)

        console.print(Panel(
            f"[bold green]Lift Report[/bold green]\n\n"
            f"Items improved: {len(improved)}/{len(bottom)} "
            f"({len(improved)/len(bottom)*100:.0f}%)\n"
            f"Average lift: {avg_lift:+.2f}\n"
            f"Per-axis: {', '.join(f'{k}: {v:+.2f}' for k, v in per_axis_lift.items())}",
            border_style="green",
        ))

        return EvalReport(
            batch_size=len(eval_items),
            judged_count=len(scored),
            avg_score=avg_score,
            per_axis_avg=per_axis_avg,
            regen_count=len(bottom),
            improved_count=len(improved),
            avg_lift=avg_lift,
            per_axis_lift=per_axis_lift,
        )

    # ------------------------------------------------------------------
    # Batch operations (parallelized)
    # ------------------------------------------------------------------

    def _judge_batch(self, items: list[EvalItem], context: Optional[str]):
        with cf.ThreadPoolExecutor(max_workers=self.eval_cfg.max_workers) as pool:
            futures = {
                pool.submit(
                    judge_item,
                    self.client,
                    it.text,
                    self.rubric,
                    self.eval_cfg.judge_model,
                    self.eval_cfg.judge_max_tokens,
                    context,
                ): it
                for it in items
            }
            done = 0
            for fut in cf.as_completed(futures):
                it = futures[fut]
                try:
                    it.judge_result = fut.result()
                except Exception as e:
                    logger.error(f"Judge failed for {it.id}: {e}")
                    it.judge_result = JudgeResult(ok=False)
                done += 1
                if done % 25 == 0:
                    console.print(f"  [dim]judged {done}/{len(items)}[/dim]")

    def _regen_batch(self, items: list[EvalItem], context: Optional[str]):
        with cf.ThreadPoolExecutor(max_workers=self.eval_cfg.max_workers) as pool:
            def _regen(it: EvalItem) -> str:
                return regenerate_item(
                    self.client,
                    it.text,
                    it.judge_result,
                    self.rubric,
                    self.eval_cfg.regen_model,
                    self.eval_cfg.regen_max_tokens,
                    context,
                )
            results = list(pool.map(_regen, items))
            for it, new_text in zip(items, results):
                it.regen_text = new_text

    def _rejudge_batch(self, items: list[EvalItem], context: Optional[str]):
        with cf.ThreadPoolExecutor(max_workers=self.eval_cfg.max_workers) as pool:
            futures = {
                pool.submit(
                    judge_item,
                    self.client,
                    it.regen_text,
                    self.rubric,
                    self.eval_cfg.judge_model,
                    self.eval_cfg.judge_max_tokens,
                    context,
                ): it
                for it in items
                if it.regen_text
            }
            for fut in cf.as_completed(futures):
                it = futures[fut]
                try:
                    it.regen_result = fut.result()
                except Exception as e:
                    logger.error(f"Re-judge failed for {it.id}: {e}")

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def _per_axis_avg(self, items: list[EvalItem]) -> dict[str, float]:
        avgs = {}
        for axis in self.rubric.axes:
            vals = [
                it.judge_result.scores.get(axis.name, 0)
                for it in items
                if it.judge_result and it.judge_result.ok
            ]
            avgs[axis.name] = sum(vals) / len(vals) if vals else 0.0
        return avgs

    def _per_axis_lift(self, items: list[EvalItem]) -> dict[str, float]:
        lifts = {}
        for axis in self.rubric.axes:
            before = [
                it.judge_result.scores.get(axis.name, 0)
                for it in items
                if it.judge_result and it.regen_result
            ]
            after = [
                it.regen_result.scores.get(axis.name, 0)
                for it in items
                if it.judge_result and it.regen_result
            ]
            if before and after:
                lifts[axis.name] = sum(after) / len(after) - sum(before) / len(before)
            else:
                lifts[axis.name] = 0.0
        return lifts

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _display_scores(self, items, per_axis_avg, avg_score):
        table = Table(title="Score Distribution")
        table.add_column("Axis", style="cyan")
        table.add_column("Mean", style="white")
        table.add_column("Min", style="red")
        table.add_column("Max", style="green")

        for axis in self.rubric.axes:
            vals = [
                it.judge_result.scores.get(axis.name, 0)
                for it in items
            ]
            table.add_row(
                axis.name,
                f"{per_axis_avg[axis.name]:.2f}",
                str(min(vals)),
                str(max(vals)),
            )
        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{avg_score:.2f}[/bold]",
            f"{min(it.judge_result.total for it in items):.0f}",
            f"{max(it.judge_result.total for it in items):.0f}",
        )
        console.print(table)
