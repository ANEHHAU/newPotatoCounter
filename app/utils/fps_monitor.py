import time
from collections import deque

class FPSMonitor:
    """
    Rolling FPS calculator for performance tracking.
    """
    def __init__(self, window_size=60):
        self.times = deque(maxlen=window_size)
    
    def tick(self):
        """
        Record a new timestamp and update rolling average.
        """
        self.times.append(time.time())
    
    @property
    def fps(self):
        """
        Compute average FPS over current window.
        """
        if len(self.times) < 2:
            return 0.0
        
        duration = self.times[-1] - self.times[0]
        if duration <= 0:
            return 0.0
        
        return (len(self.times) - 1) / duration
