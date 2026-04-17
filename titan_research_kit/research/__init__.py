"""
Deep Research Engine — Multi-pass research pipeline.

Public API:
    from titan_research_kit.research import ResearchOrchestrator
    report = ResearchOrchestrator(config).run("your question")
"""

from .orchestrator import ResearchOrchestrator

__all__ = ["ResearchOrchestrator"]
