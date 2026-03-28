import cv2
import threading
import time
import os
from ..utils.logger import ls

class FrameReader:
    """
    Thread-safe source-agnostic frame provider.
    """
    def __init__(self, source=0):
        self.source = source
        self.cap = None
        self.is_open = False
        self.lock = threading.Lock()
        
    def open(self):
        """
        Connects to video file or camera.
        """
        with self.lock:
            if self.cap is not None:
                self.cap.release()
            
            # Convert numeric strings like "0" to int for camera index
            actual_source = self.source
            if isinstance(actual_source, str):
                if actual_source.isdigit():
                    actual_source = int(actual_source)
                else:
                    actual_source = os.path.normpath(actual_source)
                
            self.cap = cv2.VideoCapture(actual_source)
            if not self.cap.isOpened():
                ls.error(f"Failed to open video source: {self.source}")
                return False
                
            self.is_open = True
            ls.info(f"Video source opened: {self.source}")
            return True

    def read(self):
        """
        Returns (success, frame).
        """
        with self.lock:
            if self.cap is None or not self.is_open:
                return False, None
            
            return self.cap.read()

    def get_fps(self):
        if self.cap:
            return self.cap.get(cv2.CAP_PROP_FPS)
        return 0.0

    def get_total_frames(self):
        if self.cap:
            return self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        return 0

    def set_pos(self, index):
        with self.lock:
            if self.cap:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)
            
    def get_pos(self):
        if self.cap:
            return self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        return 0

    def close(self):
        with self.lock:
            self.is_open = False
            if self.cap:
                self.cap.release()
                self.cap = None
