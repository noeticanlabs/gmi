"""
GM-OS Memory Layer.

Exports memory processing components:
- archive: Episodic archive for storing episodes
- replay: Memory replay functionality
- relevance: Memory relevance scoring engine
- memory_connector: Connector for integrating with hosted agent
"""

from gmos.memory import archive
from gmos.memory import replay
from gmos.memory import relevance
from gmos.memory import memory_connector

# Export commonly used classes
from gmos.memory.archive import EpisodicArchive, ArchiveState, Episode
from gmos.memory.replay import Workspace, ReplayEngine, PhantomState
from gmos.memory.relevance import MemoryRelevanceEngine, RelevanceScore
from gmos.memory.consolidation import Consolidator, ConsolidationReport, get_consolidator

__all__ = [
    "archive",
    "replay",
    "relevance",
    "memory_connector",
    # Exported classes
    "EpisodicArchive",
    "ArchiveState", 
    "Episode",
    "Workspace",
    "ReplayEngine",
    "PhantomState",
    "MemoryRelevanceEngine",
    "RelevanceScore",
    "Consolidator",
    "ConsolidationReport",
    "get_consolidator",
]
