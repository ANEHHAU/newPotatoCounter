from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
import time

class TrackState(Enum):
    NEW = auto()
    TRACKING = auto()
    IN_ROI = auto()
    IN_DEFINE_ZONE = auto()
    DEFINING = auto()
    FINALIZED = auto()
    COUNTED = auto()
    EXPIRED = auto()

class PotatoClass(Enum):
    GOOD = "GOOD"
    DAMAGED = "DAMAGED"
    DISEASED = "DISEASED"
    SPROUTED = "SPROUTED"
    DEFORMED = "DEFORMED"
    DEFECT = "DEFECT" # Catch-all for basic mode
    NA = "N/A"

@dataclass
class QualityDecision:
    class_name: PotatoClass = PotatoClass.NA
    confidence: float = 0.0
    is_final: bool = False
    timestamp: float = field(default_factory=time.time)

@dataclass
class PotatoTrack:
    track_id: int
    bbox: Tuple[float, float, float, float]  # [x, y, w, h] normalized or raw? Let's use raw pixels for drawing.
    history: List[Tuple[float, float]] = field(default_factory=list)
    state: TrackState = TrackState.NEW
    quality: QualityDecision = field(default_factory=QualityDecision)
    last_update: float = field(default_factory=time.time)
    
    # Store predictions while in the define zone for classification voting
    collected_predictions: List[Dict[str, any]] = field(default_factory=list)
    
    def add_history(self, pos: Tuple[float, float]):
        self.history.append(pos)
        if len(self.history) > 30:
            self.history.pop(0)
    
    def finalize_decision(self, operating_mode: int):
        """Analyze collected predictions and assign the final class."""
        if not self.collected_predictions:
            self.quality.class_name = PotatoClass.GOOD if operating_mode == 1 else PotatoClass.GOOD
            self.quality.confidence = 1.0
            self.quality.is_final = True
            return

        # Simple majority vote logic or highest mean confidence
        class_counts = {}
        for pred in self.collected_predictions:
            cls = pred['class']
            class_counts[cls] = class_counts.get(cls, 0) + 1
            
        # Get the most frequent class
        winner = max(class_counts, key=class_counts.get)
        self.quality.class_name = PotatoClass(winner)
        self.quality.confidence = sum(p['conf'] for p in self.collected_predictions if p['class'] == winner) / class_counts[winner]
        self.quality.is_final = True
        self.state = TrackState.FINALIZED
