"""
Novel angle generator — domain-agnostic brainstorming engine.

Generalized from anecdote-engine/tools/brainstorm_angles.py.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from rich.console import Console

from ..config import BrainstormConfig, TitanConfig
from ..models import BrainstormAngle, BrainstormResult
from ..prompts.brainstorm import BRAINSTORM_SYSTEM

logger = logging.getLogger(__name__)
console = Console()


def brainstorm_angles(
    domain: str,
    topics: dict[str, dict],
    config: Optional[TitanConfig] = None,
    brainstorm_config: Optional[BrainstormConfig] = None,
    per_topic: Optional[int] = None,
    output_dir: Optional[Path] = None,
) -> list[BrainstormResult]:
    """
    Generate novel angles for a set of topics within a domain.

    Args:
        domain: The content domain (e.g., "inspirational anecdotes", "tech blog posts").
        topics: Dict of topic_id -> topic metadata. Each topic should have:
            - keywords: list[str] (optional)
            - emotional_arc: str (optional)
            - label: str (optional)
        config: Optional TitanConfig (for API key).
        brainstorm_config: Optional BrainstormConfig overrides.
        per_topic: Override angles per topic.
        output_dir: If provided, write angle files to this directory.

    Returns:
        List of BrainstormResult, one per topic.
    """
    cfg = config or TitanConfig()
    bcfg = brainstorm_config or cfg.brainstorm
    n = per_topic or bcfg.per_topic

    client = Anthropic(api_key=cfg.anthropic_api_key)
    results = []

    for tid, tdata in topics.items():
        console.print(f"[cyan]🧠 Brainstorming {n} angles for: {tid}[/cyan]")
        result = brainstorm_topic(
            client=client,
            domain=domain,
            topic_id=tid,
            topic_data=tdata,
            per_topic=n,
            config=bcfg,
        )
        results.append(result)
        console.print(f"  → {len(result.angles)} angles generated")

        if output_dir:
            _write_angles(output_dir, result)

    total = sum(len(r.angles) for r in results)
    console.print(
        f"\n[bold green]✅ {total} angles across {len(results)} topics[/bold green]"
    )
    return results


def brainstorm_topic(
    client: Anthropic,
    domain: str,
    topic_id: str,
    topic_data: dict,
    per_topic: int = 15,
    config: Optional[BrainstormConfig] = None,
) -> BrainstormResult:
    """
    Generate novel angles for a single topic.

    Args:
        client: Anthropic API client.
        domain: Content domain description.
        topic_id: Topic identifier.
        topic_data: Topic metadata (keywords, emotional_arc, etc.).
        per_topic: Number of angles to generate.
        config: Optional BrainstormConfig.

    Returns:
        BrainstormResult with generated angles.
    """
    cfg = config or BrainstormConfig()

    # Auto-generate banned clichés based on topic
    banned = _generate_banned_cliches(topic_id, topic_data)

    system = BRAINSTORM_SYSTEM.format(
        domain=domain,
        per_topic=per_topic,
        min_words=cfg.min_word_count,
        max_words=cfg.max_word_count,
        banned_cliches="\n".join(f"- {b}" for b in banned),
    )

    keywords = topic_data.get("keywords", [])
    arc = topic_data.get("emotional_arc", "")
    label = topic_data.get("label", topic_id)

    user_msg = (
        f"TOPIC: {topic_id} — {label}\n"
        f"Emotional arc: {arc}\n"
        f"Keywords: {', '.join(keywords)}\n\n"
        f"Generate {per_topic} novel angles for this topic. "
        f"Each angle should unlock a DIFFERENT piece of content — "
        f"different contexts, different stakes, different perspectives."
    )

    try:
        response = client.messages.create(
            model=cfg.model,
            max_tokens=cfg.max_tokens,
            temperature=cfg.temperature,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as e:
        logger.error(f"Brainstorm API error for {topic_id}: {e}")
        return BrainstormResult(
            topic_id=topic_id,
            domain=domain,
            banned_cliches=banned,
        )

    raw = response.content[0].text.strip()

    # Parse JSON response
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not json_match:
        logger.warning(f"No JSON in brainstorm response for {topic_id}")
        return BrainstormResult(
            topic_id=topic_id,
            domain=domain,
            banned_cliches=banned,
        )

    try:
        data = json.loads(json_match.group(0))
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in brainstorm response for {topic_id}")
        return BrainstormResult(
            topic_id=topic_id,
            domain=domain,
            banned_cliches=banned,
        )

    angles = [
        BrainstormAngle(
            title=a.get("title", f"angle-{i}"),
            text=a.get("text", ""),
            topic_id=topic_id,
            domain=domain,
        )
        for i, a in enumerate(data.get("angles", [])[:per_topic])
    ]

    return BrainstormResult(
        topic_id=topic_id,
        domain=domain,
        angles=angles,
        banned_cliches=banned,
    )


def _generate_banned_cliches(topic_id: str, topic_data: dict) -> list[str]:
    """Generate obvious clichés to ban based on the topic."""
    # These are common across most inspirational/motivational content
    generic_bans = [
        "Generic 'never give up' framing",
        "Standard 'trust the process' messaging",
        "Typical rags-to-riches billionaire story",
    ]

    # Add topic-specific bans from metadata if provided
    specific_bans = topic_data.get("avoid", [])

    return generic_bans + specific_bans


def _slugify(s: str, n: int = 50) -> str:
    """Convert a string to a URL-friendly slug."""
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", s).strip().lower()
    return re.sub(r"\s+", "-", s)[:n] or "angle"


def _write_angles(output_dir: Path, result: BrainstormResult) -> None:
    """Write angles to disk as markdown files."""
    topic_dir = output_dir / result.topic_id
    topic_dir.mkdir(parents=True, exist_ok=True)

    for i, angle in enumerate(result.angles):
        fname = f"angle-{i:02d}-{_slugify(angle.title)}.md"
        path = topic_dir / fname
        content = "\n".join([
            "---",
            f"source_author: Brainstorm",
            f"source_sub: _novel",
            f"topic_id: {angle.topic_id}",
            f"angle: {json.dumps(angle.title)}",
            f"domain: {json.dumps(angle.domain)}",
            "kind: novel_angle",
            "---",
            "",
            f"# {angle.title}",
            "",
            angle.text.strip(),
            "",
        ])
        path.write_text(content)
