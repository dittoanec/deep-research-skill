"""
Brainstorm Engine — Novel angle generation.

Public API:
    from titan_research_kit.brainstorm import brainstorm_angles
    angles = brainstorm_angles(domain="...", topics={...})
"""

from .angles import brainstorm_angles, brainstorm_topic

__all__ = ["brainstorm_angles", "brainstorm_topic"]
