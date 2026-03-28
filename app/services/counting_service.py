import numpy as np
import cv2
from ..utils.logger import ls

class CountingService:
    """
    Handles counting line-crossing logic.
    """
    def __init__(self, counting_line=None):
        """
        counting_line: [[x1,y1], [x2,y2]] (normalized 0-1)
        """
        self.line = counting_line
        self.counts = {
            "Total": 0,
            "GOOD": 0,
            "DEFECT": 0,
            "damaged": 0,
            "diseased": 0,
            "sprouted": 0,
            "deformed": 0,
            "unknown": 0
        }
        self.crossed_ids = set() # {track_id} to avoid double counting

    def set_line(self, line):
        self.line = line
        self.reset_counts()
        ls.info(f"Counting line set: {line}")

    def reset_counts(self):
        for k in self.counts: self.counts[k] = 0
        self.crossed_ids.clear()
        
    def check_crossing(self, track_id, previous_point, current_point):
        """
        Checks if a centroid move from prev to curr crosses our line.
        """
        if not self.line or previous_point is None or current_point is None:
            return False
            
        if track_id in self.crossed_ids:
            return False
            
        # Line-crossing logic: CCW/intersect test
        p1 = np.array(self.line[0])
        p2 = np.array(self.line[1])
        A = previous_point
        B = current_point
        
        def ccw(A,B,C):
            return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

        # Standard Segment-Segment intersection test
        intersect = ccw(A,p1,p2) != ccw(B,p1,p2) and ccw(A,B,p1) != ccw(A,B,p2)
        
        if intersect:
            self.crossed_ids.add(track_id)
            return True
        return False

    def increment(self, label):
        """
        Increments internal stats.
        """
        self.counts["Total"] += 1
        if label in self.counts:
            self.counts[label] += 1
        else:
            # Fallback for dynamic classes
            self.counts[label] = self.counts.get(label, 0) + 1
            
    def get_stats(self):
        return self.counts.copy()
