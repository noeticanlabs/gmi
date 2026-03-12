# Sensory/Memory World-Weld Design Specification

> **Status**: Design Draft  
> **Priority**: High  
> **Gap**: Missing external I/O hooks for real sensor telemetry

## Overview

The "World-Weld" refers to the external I/O connectors that bridge GM-OS with real-world sensor telemetry and complex external data sources. This document outlines the design for sensory and memory I/O hooks.

## Current State

Existing modules:
- [`gmos/src/gmos/sensory/manifold.py`](gmos/src/gmos/sensory/manifold.py) - Defines sensory charts (External, Semantic, Internal)
- [`gmos/src/gmos/memory/archive.py`](gmos/src/gmos/memory/archive.py) - Episodic memory storage
- [`gmos/src/gmos/memory/workspace.py`](gmos/src/gmos/memory/workspace.py) - Active phantom states

**Current Gap**: These modules lack external I/O hooks to stream real sensor data or connect to external databases.

## Design Requirements

### 1. Sensory Connector Interface

```python
class SensoryConnector(ABC):
    """
    Abstract base for sensory data ingestion.
    
    Responsibilities:
    1. Stream sensor telemetry
    2. Convert to ExternalChart format
    3. Handle modality multiplexing
    4. Manage temporal alignment
    """
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to sensor source."""
        ...
    
    @abstractmethod
    def read(self) -> ExternalChart:
        """Read latest sensor data."""
        ...
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection."""
        ...
```

### 2. Implemented Connector Types

| Connector | Description |
|-----------|-------------|
| `FileSensoryConnector` | Read from file-based sensor logs |
| `MQTTSensoryConnector` | Stream from MQTT topics |
| `WebSocketSensoryConnector` | Real-time web sensor streams |
| `DatabaseSensoryConnector` | Query external database schemas |

### 3. Memory Connector Interface

```python
class MemoryConnector(ABC):
    """
    Abstract base for external memory storage.
    
    Responsibilities:
    1. Persist episodes to external storage
    2. Query historical episodes
    3. Handle schema evolution
    4. Manage transactional consistency
    """
    
    @abstractmethod
    def store_episode(self, episode: Episode) -> str:
        """Store episode, return external ID."""
        ...
    
    @abstractmethod
    def retrieve_episode(self, episode_id: str) -> Optional[Episode]:
        """Retrieve episode by ID."""
        ...
    
    @abstractmethod
    def query_episodes(self, query: MemoryQuery) -> List[Episode]:
        """Query episodes by criteria."""
        ...
```

### 4. Integration with Sensory Manifold

```python
class SensoryFusion:
    """
    Fuses multiple sensory inputs into unified state.
    
    Flow:
    1. Each connector reads its modality
    2. Fusion weights modalities by confidence
    3. Outputs unified ExternalChart
    """
    
    def __init__(self):
        self._connectors: Dict[ModalityType, SensoryConnector] = {}
    
    def register_connector(self, modality: ModalityType, connector: SensoryConnector):
        """Register a modality connector."""
        ...
    
    def fuse(self) -> ExternalChart:
        """Fuse all registered modalities."""
        ...
```

### 5. Configuration Schema

```yaml
sensory:
  connectors:
    - type: mqtt
      topic: "sensors/vision"
      modality: vision
      confidence: 0.9
    - type: mqtt
      topic: "sensors/audio"  
      modality: audio
      confidence: 0.7

memory:
  connector:
    type: postgresql
    connection_string: "${MEMORY_DB_URL}"
    schema_version: 1
```

## Implementation Plan

### Phase 1: Abstract Interfaces
- [ ] Define `SensoryConnector` ABC
- [ ] Define `MemoryConnector` ABC
- [ ] Define configuration schema

### Phase 2: File-Based Connectors
- [ ] Implement `FileSensoryConnector`
- [ ] Implement `FileMemoryConnector`

### Phase 3: Network Connectors
- [ ] Implement `MQTTSensoryConnector`
- [ ] Implement `WebSocketSensoryConnector`

### Phase 4: Fusion & Integration
- [ ] Implement `SensoryFusion`
- [ ] Integrate with `substrate_state.py`

## Related Files

- [`gmos/src/gmos/sensory/manifold.py`](gmos/src/gmos/sensory/manifold.py) - Current sensory state
- [`gmos/src/gmos/sensory/sensory_connector.py`](gmos/src/gmos/sensory/sensory_connector.py) - Existing connector stub
- [`gmos/src/gmos/memory/memory_connector.py`](gmos/src/gmos/memory/memory_connector.py) - Existing memory connector stub
- [`gmos/src/gmos/sensory/fusion.py`](gmos/src/gmos/sensory/fusion.py) - Existing fusion stub

## Notes

- Connectors should handle reconnection gracefully
- Temporal alignment is critical for multi-modal fusion
- Schema evolution must be backward compatible
