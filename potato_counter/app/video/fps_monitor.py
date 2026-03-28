import time
from collections import deque

class FPSMonitor:
    """Helper to track and calculate frame-per-second values."""
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.timestamps = deque(maxlen=window_size)

    def tick(self):
        """Register a new frame timestamp."""
        self.timestamps.append(time.time())

    def get_fps(self) -> float:
        """Calculate the average FPS over the configured window."""
        if len(self.timestamps) < 2:
            return 0.0
        
        duration = self.timestamps[-1] - self.timestamps[0]
        if duration <= 0:
            return 0.0
            
        return (len(self.timestamps) - 1) / duration

    def reset(self):
        self.timestamps.clear()
