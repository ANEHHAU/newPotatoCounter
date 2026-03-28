from collections import deque
import numpy as np
from ..utils.logger import ls

class ConveyorSpeedService:
    """
    Estimates belt speed using centroid displacement of tracked objects.
    """
    def __init__(self, mm_per_pixel=1.0, smoothing_window=30):
        self.mm_per_pixel = mm_per_pixel
        self.deltas = deque(maxlen=smoothing_window)
        self.calibrated = False
        
    def update(self, tracks, actual_fps):
        """
        Updates speed estimates using active track displacements.
        """
        if actual_fps <= 0 or not tracks:
            # Maintain last known or default to 0
            return 0.0
            
        frame_deltas = []
        for track in tracks:
            if not track.bbox_history or len(track.bbox_history) < 2:
                continue
                
            # Get latest two centroids
            curr_box = track.bbox_history[-1]
            prev_box = track.bbox_history[-2]
            
            curr_c = ((curr_box[0]+curr_box[2])/2, (curr_box[1]+curr_box[3])/2)
            prev_c = ((prev_box[0]+prev_box[2])/2, (prev_box[1]+prev_box[3])/2)
            
            # Displacement magnitude (pixels)
            # Usually conveyor moves in Y or X direction mainly, use Euclidean for general belt motion
            dist = np.sqrt((curr_c[0]-prev_c[0])**2 + (curr_c[1]-prev_c[1])**2)
            frame_deltas.append(dist)
            
        if frame_deltas:
            # Average delta (px/frame)
            avg_delta_px = np.mean(frame_deltas)
            # Convert to px/sec
            px_per_sec = avg_delta_px * actual_fps
            self.deltas.append(px_per_sec)
        
    @property
    def speed_px_per_sec(self):
        if not self.deltas: return 0.0
        return np.mean(self.deltas)
        
    @property
    def speed_mm_per_sec(self):
        return self.speed_px_per_sec * self.mm_per_pixel
        
    @property
    def speed_display(self):
        v_px = self.speed_px_per_sec
        v_mm = self.speed_mm_per_sec
        
        if self.calibrated:
            if v_mm > 1000:
                return f"{v_mm/1000.0:.2f} m/s"
            else:
                return f"{v_mm/10.0:.1f} cm/s"
        else:
            return f"{v_px:.1f} px/s"

    def set_calibration(self, enabled, mm_per_pixel):
        self.calibrated = enabled
        self.mm_per_pixel = mm_per_pixel
