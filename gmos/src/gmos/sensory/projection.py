"""
Projection for GM-OS Sensory Manifold.

Maps raw observations into manifold coordinates:
- project_world_state() -> ExternalChart
- project_internal_state() -> InternalChart

Projection preserves:
- source traceability
- uncertainty/confidence
- timestamp alignment
"""

from typing import Dict, Any, Optional, List
import time

from gmos.sensory.manifold import (
    ExternalChart,
    InternalChart,
    ModalityType,
    SensoryState,
    create_sensory_state
)


def project_world_state(
    observation: Dict[str, Any],
    modalities: Optional[List[str]] = None
) -> ExternalChart:
    """
    Project raw world observation into external manifold coordinates.
    
    Args:
        observation: Raw observation from environment
            May include:
            - tool outputs
            - image/audio features
            - event streams
            - simulation states
            - environment metadata
        modalities: Optional list of modality types to extract
        
    Returns:
        ExternalChart with projected coordinates, confidence, source tags
    """
    chart = ExternalChart()
    chart.timestamp = observation.get("timestamp", time.time())
    
    # Extract modality data
    raw_modalities = observation.get("modalities", {})
    for mod_name, mod_data in raw_modalities.items():
        if modalities and mod_name not in modalities:
            continue
        try:
            mod_type = ModalityType(mod_name)
        except ValueError:
            mod_type = ModalityType.TOOL  # Default
        chart.modalities[mod_type] = mod_data
    
    # Extract objects
    chart.objects = observation.get("objects", [])
    
    # Extract events
    chart.events = observation.get("events", [])
    
    # Extract spatial features
    chart.locations = observation.get("locations", {})
    chart.motions = observation.get("motions", {})
    
    # Extract confidence
    chart.confidence = observation.get("confidence", 0.8)
    
    # Extract uncertainty
    chart.uncertainty = observation.get("uncertainty", {})
    
    # Extract window
    chart.window_start = observation.get("window_start", chart.timestamp - 1.0)
    chart.window_end = observation.get("window_end", chart.timestamp)
    
    # Extract source tags
    chart.source_tags = observation.get("sources", ["world"])
    
    return chart


def project_internal_state(
    budget: float,
    reserve: float,
    pressure: float = 0.0,
    threat: float = 0.0,
    mode: str = "active",
    load: Optional[Dict[str, float]] = None,
    memory_load: float = 0.0,
    replay_count: int = 0,
    active_processes: int = 1,
    additional_metrics: Optional[Dict[str, Any]] = None
) -> InternalChart:
    """
    Project internal system state into internal manifold coordinates.
    
    Args:
        budget: Current budget amount
        reserve: Reserved budget (protected)
        pressure: Current pressure level
        threat: Current threat level
        mode: Current operational mode
        load: Layer-specific load metrics
        memory_load: Current memory pressure
        replay_count: Number of active replays
        active_processes: Number of active processes
        additional_metrics: Additional internal metrics
        
    Returns:
        InternalChart with mapped internal state
    """
    chart = InternalChart()
    chart.timestamp = time.time()
    
    # Budget metrics
    chart.budget = budget
    chart.reserve = reserve
    chart.available = max(0, budget - reserve)
    
    # Pressure metrics
    chart.pressure = pressure
    chart.load = load or {}
    
    # Threat/affect shell
    chart.threat_level = threat
    # Compute freeze and greed from budget state
    if budget <= reserve:
        chart.freeze_level = 1.0
        chart.greed_level = 0.0
    elif budget < reserve * 2:
        chart.freeze_level = 0.5
        chart.greed_level = 0.0
    else:
        chart.freeze_level = 0.0
        # Greed increases with excess budget
        excess_ratio = (budget - reserve * 2) / (reserve * 2)
        chart.greed_level = min(1.0, excess_ratio)
    
    # Process health
    chart.active_processes = active_processes
    chart.mode = mode
    # Health decreases with pressure and threat
    chart.health_score = max(0, min(1.0, 1.0 - pressure * 0.5 - threat * 0.3))
    
    # Memory metrics
    chart.memory_load = memory_load
    chart.replay_count = replay_count
    
    # Additional metrics
    if additional_metrics:
        for key, value in additional_metrics.items():
            if hasattr(chart, key):
                setattr(chart, key, value)
    
    return chart


def project_from_gmi_state(
    gmi_state: Dict[str, Any]
) -> InternalChart:
    """
    Project GMI agent state into internal chart.
    
    Args:
        gmi_state: State dictionary from GMI agent
        
    Returns:
        InternalChart
    """
    return project_internal_state(
        budget=gmi_state.get("budget", 0.0),
        reserve=gmi_state.get("reserve", 0.0),
        pressure=gmi_state.get("pressure", 0.0),
        threat=gmi_state.get("threat", 0.0),
        mode=gmi_state.get("mode", "unknown"),
        load=gmi_state.get("load", {}),
        memory_load=gmi_state.get("memory_load", 0.0),
        replay_count=gmi_state.get("replay_count", 0),
        active_processes=gmi_state.get("active_processes", 1)
    )


def create_projection(
    world_obs: Dict[str, Any],
    internal_state: Dict[str, Any],
    semantic_data: Optional[Dict[str, Any]] = None
) -> SensoryState:
    """
    Create complete sensory state from world and internal projections.
    
    Args:
        world_obs: Raw world observation
        internal_state: GMI/internal state dictionary
        semantic_data: Optional semantic data
        
    Returns:
        Complete SensoryState
    """
    # Project world state
    external = project_world_state(world_obs)
    
    # Project internal state
    internal = project_from_gmi_state(internal_state)
    
    # Build sensory state
    return create_sensory_state(
        external={
            "modalities": {k.value: v for k, v in external.modalities.items()},
            "objects": external.objects,
            "events": external.events,
            "confidence": external.confidence,
            "timestamp": external.timestamp,
            "sources": external.source_tags,
        },
        internal=internal.to_dict(),
        semantic=semantic_data
    )
