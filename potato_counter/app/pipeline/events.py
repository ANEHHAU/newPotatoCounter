from dataclasses import dataclass
from typing import Optional, List, Dict
import numpy as np
from ..domain.potato_track import PotatoTrack

@dataclass
class FrameCapturedEvent:
    frame: np.ndarray
    timestamp: float
    frame_idx: int

@dataclass
class ProcessingResults:
    original_frame: np.ndarray
    processed_frame: np.ndarray
    tracks: List[PotatoTrack]
    stats: any # CountingStats
    fps: float
    input_fps: float
    conveyor_speed: float
    timestamp: float
