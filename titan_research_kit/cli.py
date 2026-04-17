"""
CLI entry point for Titan Research Kit.

Usage:
    python -m titan_research_kit research "What is the best approach to X?"
    python -m titan_research_kit brainstorm --domain "content creation" --topics topic1,topic2
    python -m titan_research_kit eval --input outputs/*.txt --rubric content --regen-bottom 0.25
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console

from .config import TitanConfig

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Titan Research Kit — Deep Research, Eval Loop, Brainstorm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m titan_research_kit research "What is the best database for time-series data?"
  python -m titan_research_kit brainstorm --domain "blog posts" --topics ai,leadership --per-topic 10
  python -m titan_research_kit eval --input batch.txt --rubric content --regen-bottom 0.25
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Research ---
    research_parser = subparsers.add_parser(
        "research", help="Run multi-pass deep research"
    )
    research_parser.add_argument("query", help="The research question")
    research_parser.add_argument(
        "--max-passes", type=int, default=3, help="Max research passes (default: 3)"
    )
    research_parser.add_argument(
        "--output", type=str, default="./research_output", help="Output directory"
    )
    research_parser.add_argument(
        "--pause", action="store_true", help="Pause for human review after first challenger pass"
    )

    # --- Brainstorm ---
    brainstorm_parser = subparsers.add_parser(
        "brainstorm", help="Generate novel angles for topics"
    )
    brainstorm_parser.add_argument(
        "--domain", required=True, help="Content domain (e.g., 'inspirational anecdotes')"
    )
    brainstorm_parser.add_argument(
        "--topics", required=True, help="Comma-separated topic IDs"
    )
    brainstorm_parser.add_argument(
        "--taxonomy", type=str, help="Path to taxonomy.json with topic metadata"
    )
    brainstorm_parser.add_argument(
        "--per-topic", type=int, default=15, help="Angles per topic (default: 15)"
    )
    brainstorm_parser.add_argument(
        "--output", type=str, default="./brainstorm_output", help="Output directory"
    )

    # --- Eval ---
    eval_parser = subparsers.add_parser(
        "eval", help="Judge and improve a batch of outputs"
    )
    eval_parser.add_argument(
        "--input", required=True, help="Path to input file (one item per line, or JSON array)"
    )
    eval_parser.add_argument(
        "--rubric", default="content",
        choices=["content", "research", "code"],
        help="Rubric preset (default: content)"
    )
    eval_parser.add_argument(
        "--regen-bottom", type=float, default=0.25,
        help="Fraction of bottom items to regenerate (default: 0.25)"
    )
    eval_parser.add_argument(
        "--workers", type=int, default=4, help="Parallel workers (default: 4)"
    )
    eval_parser.add_argument(
        "--output", type=str, default="./eval_output", help="Output directory"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = TitanConfig()
    errors = config.validate()
    if errors:
        for e in errors:
            console.print(f"[red]❌ {e}[/red]")
        sys.exit(1)

    if args.command == "research":
        _run_research(args, config)
    elif args.command == "brainstorm":
        _run_brainstorm(args, config)
    elif args.command == "eval":
        _run_eval(args, config)


def _run_research(args, config: TitanConfig):
    from .research import ResearchOrchestrator

    config.research.max_passes = args.max_passes
    config.research.output_dir = Path(args.output)
    config.research.pause_after_first_challenge = args.pause

    orchestrator = ResearchOrchestrator(config=config)
    report = orchestrator.run(args.query)

    console.print(f"\n[bold green]✅ Report saved to {args.output}/[/bold green]")


def _run_brainstorm(args, config: TitanConfig):
    from .brainstorm import brainstorm_angles

    topic_ids = [t.strip() for t in args.topics.split(",")]

    # Build topics dict from taxonomy or minimal structure
    if args.taxonomy:
        taxonomy = json.loads(Path(args.taxonomy).read_text())
        topics = {
            tid: taxonomy.get("topics", {}).get(tid, {"label": tid})
            for tid in topic_ids
        }
    else:
        topics = {tid: {"label": tid, "keywords": []} for tid in topic_ids}

    config.brainstorm.per_topic = args.per_topic
    output_dir = Path(args.output)

    results = brainstorm_angles(
        domain=args.domain,
        topics=topics,
        config=config,
        output_dir=output_dir,
    )

    total = sum(len(r.angles) for r in results)
    console.print(
        f"\n[bold green]✅ {total} angles written to {output_dir}/[/bold green]"
    )


def _run_eval(args, config: TitanConfig):
    from .eval import EvalLoop, CONTENT_RUBRIC, RESEARCH_RUBRIC, CODE_RUBRIC

    rubric_map = {
        "content": CONTENT_RUBRIC,
        "research": RESEARCH_RUBRIC,
        "code": CODE_RUBRIC,
    }
    rubric = rubric_map[args.rubric]

    # Load items
    input_path = Path(args.input)
    if not input_path.exists():
        console.print(f"[red]File not found: {args.input}[/red]")
        sys.exit(1)

    raw = input_path.read_text()
    try:
        items = json.loads(raw)
        if isinstance(items, list):
            items = [str(i) if not isinstance(i, str) else i for i in items]
        else:
            items = [line.strip() for line in raw.split("\n") if line.strip()]
    except json.JSONDecodeError:
        items = [line.strip() for line in raw.split("\n") if line.strip()]

    config.eval.regen_fraction = args.regen_bottom
    config.eval.max_workers = args.workers

    loop = EvalLoop(rubric=rubric, config=config)
    report = loop.run(items)

    # Save report
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "eval_report.json"
    report_path.write_text(report.model_dump_json(indent=2))
    console.print(f"\n[bold green]✅ Report saved to {report_path}[/bold green]")


if __name__ == "__main__":
    main()
