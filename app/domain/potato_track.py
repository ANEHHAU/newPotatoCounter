import numpy as np
import time
from enum import Enum, auto

class PotatoState(Enum):
    NEW = auto()
    TRACKING = auto()
    IN_ROI = auto()
    IN_DEFINE_ZONE = auto()
    FINALIZING = auto()
    FINALIZED = auto()
    COUNTED = auto()
    EXPIRED = auto()

class PotatoTrack:
    """
    Core entity representing a tracked object through its lifecycle.
    """
    def __init__(self, track_id):
        self.track_id = track_id
        self.state = PotatoState.NEW
        self.bbox_history = []  # list of [x1,y1,x2,y2]
        self.prediction_history = []  # list of [(class_id, conf)]
        
        # Results
        self.final_label = "N/A"
        self.final_confidence = 0.0
        self.decision_reason = "Idle"
        self.frames_in_zone = 0
        self.entry_time = None
        self.exit_time = None
        
        self.snapshot = None
        self.last_centroid = None  # For speed estimation

    def update_state(self, is_in_roi, is_in_define_zone, crossed_line):
        """
        State machine transition logic.
        """
        # NEW -> TRACKING
        if self.state == PotatoState.NEW:
            self.state = PotatoState.TRACKING
            
        # TRACKING -> IN_ROI
        if self.state == PotatoState.TRACKING and is_in_roi:
            self.state = PotatoState.IN_ROI
            
        # IN_ROI -> IN_DEFINE_ZONE
        if self.state == PotatoState.IN_ROI and is_in_define_zone:
            self.state = PotatoState.IN_DEFINE_ZONE
            if self.entry_time is None:
                self.entry_time = time.time()
                
        # IN_DEFINE_ZONE -> FINALIZING
        if self.state == PotatoState.IN_DEFINE_ZONE and not is_in_define_zone:
            self.state = PotatoState.FINALIZING
            self.exit_time = time.time()
            # Logic here to finalize via classification_service later
            
        # FINALIZING -> FINALIZED happens in classification service once vote is done
        
        # FINALIZED -> COUNTED
        if (self.state == PotatoState.FINALIZED or self.state == PotatoState.IN_DEFINE_ZONE or self.state == PotatoState.FINALIZING) and crossed_line:
            self.state = PotatoState.COUNTED

    def add_prediction(self, class_id, conf):
        """
        Collect class and confidence for temporal voting.
        """
        if self.state == PotatoState.IN_DEFINE_ZONE:
            self.prediction_history.append((class_id, conf))
            self.frames_in_zone += 1
            
    def set_snapshot_if_closer_to_center(self, frame_patch, bbox):
        """
        Updates snapshot if current bbox is more 'central' for best quality.
        Wait for IN_DEFINE_ZONE for best view.
        """
        if self.state == PotatoState.IN_DEFINE_ZONE:
            self.snapshot = frame_patch

    def __repr__(self):
        return f"<PotatoTrack ID:{self.track_id} State:{self.state.name} Label:{self.final_label}>"
