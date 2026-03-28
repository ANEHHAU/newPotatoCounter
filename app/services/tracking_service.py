import supervision as sv
import numpy as np
from ..utils.logger import ls

class TrackingService:
    """
    ByteTrack integration for stable object tracking.
    Compatible with Supervision 0.18 - 0.27+
    """
    def __init__(self, frame_rate=30, track_thresh=0.25, track_buffer=30, match_thresh=0.8):
        self.frame_rate = frame_rate
        self.track_thresh = track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        
        # Supervision tracker initialization (handling API changes)
        self.tracker = self._init_tracker()
        
    def _init_tracker(self):
        try:
            # Modern versions (0.24+)
            return sv.ByteTrack(
                track_activation_threshold=self.track_thresh,
                lost_track_buffer=self.track_buffer,
                minimum_matching_threshold=self.match_thresh,
                frame_rate=self.frame_rate
            )
        except TypeError:
            try:
                # Older versions (0.18 - 0.23)
                return sv.ByteTrack(
                    track_thresh=self.track_thresh,
                    track_buffer=self.track_buffer,
                    match_thresh=self.match_thresh,
                    frame_rate=self.frame_rate
                )
            except Exception as e:
                ls.error(f"Failed to initialize ByteTrack: {e}")
                return None
            
    def update(self, detections_raw):
        """
        Input: List of {'bbox': [x1,y1,x2,y2], 'conf': f, 'class_id': i}
        Output:
            ids: List[int]
            detections_by_id: Dict mapping id to detection data
        """
        if self.tracker is None:
            return [], {}

        if not detections_raw:
            sv_detections = sv.Detections.empty()
        else:
            xyxy = np.array([d['bbox'] for d in detections_raw], dtype=np.float32)
            confidence = np.array([d['conf'] for d in detections_raw], dtype=np.float32)
            class_id = np.array([d['class_id'] for d in detections_raw], dtype=np.int32)
            
            sv_detections = sv.Detections(
                xyxy=xyxy,
                confidence=confidence,
                class_id=class_id
            )
            
        # Tracker update
        tracked_detections = self.tracker.update_with_detections(sv_detections)
        
        # Check if tracker_id attribute exists and is not empty
        if len(tracked_detections) == 0 or tracked_detections.tracker_id is None:
            return [], {}
            
        ids = tracked_detections.tracker_id.tolist()
        
        detections_by_id = {}
        for i, tid in enumerate(ids):
            detections_by_id[tid] = {
                'bbox': tracked_detections.xyxy[i].tolist(),
                'conf': float(tracked_detections.confidence[i]),
                'class_id': int(tracked_detections.class_id[i])
            }
            
        return ids, detections_by_id

    def reset(self):
        """
        Necessary on seek to avoid ID collisions and ghost tracks.
        """
        self.tracker = self._init_tracker()
        ls.info("Tracking service reset.")
