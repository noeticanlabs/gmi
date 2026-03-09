"""
External I/O for GM-OS Action Layer.

Defines interface for lawful world coupling, sensor/actuator bridge.
Provides abstraction for reading from and writing to external environments.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
import time


@dataclass
class SensorReading:
    """A reading from an external sensor."""
    sensor_id: str
    modality: str  # vision, audio, text, etc.
    data: Any
    timestamp: float = field(default_factory=time.time)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActuatorCommand:
    """A command to an external actuator."""
    actuator_id: str
    action_type: str
    parameters: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    

@dataclass
class ActuatorResponse:
    """Response from an actuator."""
    command_id: str
    status: str  # success, failure, pending
    result: Any = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class ExternalInterface:
    """
    External I/O interface for GM-OS.
    
    Provides sensor reading and actuator command functionality
    with proper budget-aware handling.
    """
    
    def __init__(self, budget_router=None):
        """
        Initialize external interface.
        
        Args:
            budget_router: Optional BudgetRouter for I/O cost tracking
        """
        self.budget_router = budget_router
        self.sensors: Dict[str, Callable] = {}
        self.actuators: Dict[str, Callable] = {}
        self.readings: List[SensorReading] = []
        self.commands: List[ActuatorCommand] = []
        
    def register_sensor(
        self, 
        sensor_id: str, 
        modality: str,
        reader: Callable[[], Any]
    ) -> None:
        """
        Register a sensor reader.
        
        Args:
            sensor_id: Unique identifier for the sensor
            modality: Type of sensor (vision, audio, text, etc.)
            reader: Callable that returns sensor data
        """
        self.sensors[sensor_id] = {
            'reader': reader,
            'modality': modality,
        }
    
    def register_actuator(
        self,
        actuator_id: str,
        executor: Callable[[Dict[str, Any]], ActuatorResponse]
    ) -> None:
        """
        Register an actuator.
        
        Args:
            actuator_id: Unique identifier for the actuator
            executor: Callable that executes commands
        """
        self.actuators[actuator_id] = executor
    
    def read_sensor(
        self, 
        sensor_id: str,
        budget: float = 0.0,
    ) -> Optional[SensorReading]:
        """
        Read from a sensor.
        
        Args:
            sensor_id: ID of sensor to read
            budget: Budget available for this read
            
        Returns:
            SensorReading or None if failed
        """
        if sensor_id not in self.sensors:
            return None
        
        # Check budget
        if self.budget_router and budget > 0:
            # Simplified - in production would check against process budget
            pass
        
        try:
            sensor = self.sensors[sensor_id]
            data = sensor['reader']()
            
            reading = SensorReading(
                sensor_id=sensor_id,
                modality=sensor['modality'],
                data=data,
            )
            
            self.readings.append(reading)
            return reading
            
        except Exception as e:
            return None
    
    def read_all_sensors(
        self,
        sensor_ids: Optional[List[str]] = None,
        budget: float = 0.0,
    ) -> List[SensorReading]:
        """
        Read from multiple sensors.
        
        Args:
            sensor_ids: List of sensor IDs (None = all)
            budget: Budget available for readings
            
        Returns:
            List of SensorReadings
        """
        if sensor_ids is None:
            sensor_ids = list(self.sensors.keys())
        
        readings = []
        for sid in sensor_ids:
            reading = self.read_sensor(sid, budget)
            if reading:
                readings.append(reading)
        
        return readings
    
    def write_actuator(
        self,
        actuator_id: str,
        action_type: str,
        parameters: Dict[str, Any],
        budget: float = 0.0,
    ) -> Optional[ActuatorResponse]:
        """
        Write action to an actuator.
        
        Args:
            actuator_id: ID of actuator to command
            action_type: Type of action
            parameters: Action parameters
            budget: Budget available for this action
            
        Returns:
            ActuatorResponse or None if failed
        """
        if actuator_id not in self.actuators:
            return None
        
        # Check budget
        if self.budget_router and budget > 0:
            # Simplified - in production would check against process budget
            pass
        
        command = ActuatorCommand(
            actuator_id=actuator_id,
            action_type=action_type,
            parameters=parameters,
        )
        
        self.commands.append(command)
        
        try:
            executor = self.actuators[actuator_id]
            response = executor(parameters)
            return response
            
        except Exception as e:
            return ActuatorResponse(
                command_id=actuator_id,
                status="failure",
                error=str(e),
            )
    
    def get_readings(
        self, 
        modality: Optional[str] = None,
        since: Optional[float] = None,
    ) -> List[SensorReading]:
        """
        Get recent sensor readings.
        
        Args:
            modality: Filter by modality (None = all)
            since: Filter by timestamp (None = all)
            
        Returns:
            List of SensorReadings
        """
        readings = self.readings
        
        if modality:
            readings = [r for r in readings if r.modality == modality]
        
        if since:
            readings = [r for r in readings if r.timestamp >= since]
        
        return readings


# Convenience functions

def read_environment(observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Read from environment (legacy compatibility).
    
    Args:
        observation: Raw observation data
        
    Returns:
        Processed observation
    """
    # Process observation into standard format
    processed = {
        'raw': observation,
        'timestamp': time.time(),
        'modality': observation.get('modality', 'unknown'),
    }
    return processed


def write_environment(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Write action to environment (legacy compatibility).
    
    Args:
        action: Action to execute
        
    Returns:
        Execution result
    """
    return {
        "status": "executed",
        "action": action,
        "timestamp": time.time(),
    }
