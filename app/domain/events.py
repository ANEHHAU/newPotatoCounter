from dataclasses import dataclass
import numpy as np

@dataclass
class PotatoCountedEvent:
    """
    Emitted when a potato crosses the counting line.
    """
    track_id: int
    final_label: str
    final_confidence: float
    decision_reason: str
    frames_in_zone: int
    snapshot: np.ndarray = None

@dataclass
class PotatoFinalizedEvent:
    """
    Emitted when a potato exits the define zone and its label is finalized.
    """
    track_id: int
    final_label: str
    final_confidence: float
    decision_reason: str
    frames_in_zone: int
    snapshot: np.ndarray = None

@dataclass
class QualityUpdateEvent:
    """
    Sent to UI for refreshing statistics.
    """
    total: int
    good: int
    defect: int
    class_breakdown: dict
    belt_speed: str
    defect_rate: float
