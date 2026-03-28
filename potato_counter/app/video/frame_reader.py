import cv2
import threading
from typing import Optional, Tuple
import time

class FrameReader:
    """Handles low-level frame reading from video file or camera."""
    def __init__(self, source: str = "default"):
        self.source = 0 if source == "default" or source == "0" else source
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_camera = isinstance(self.source, int)
        
        # Metadata
        self.fps = 30.0
        self.total_frames = 0
        self.width = 1920
        self.height = 1080
        self.opened = False

    def open(self) -> bool:
        """Opens the source and initializes video properties."""
        if self.cap:
            self.cap.release()
            
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            print(f"[Error] Could not open source: {self.source}")
            return False
        
        self.opened = True
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        # Avoid zero FPS for camera
        if self.fps <= 0:
            self.fps = 30.0
            
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) if not self.is_camera else -1
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Potentially set resolution if camera
        if self.is_camera:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            
        return True

    def read(self) -> Tuple[bool, Optional[cv2.Mat]]:
        """Reads a single frame from the source."""
        if not self.cap or not self.opened:
            return False, None
        return self.cap.read()

    def set_frame_index(self, index: int):
        """Seek to a specific frame index (for files only)."""
        if self.cap and not self.is_camera:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)

    def get_frame_index(self) -> int:
        if self.cap and not self.is_camera:
            return int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        return 0

    def close(self):
        if self.cap:
            self.cap.release()
            self.opened = False
        self.cap = None
