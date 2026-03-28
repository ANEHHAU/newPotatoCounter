import cv2
import numpy as np
from ..utils.logger import ls

def get_snapshot_bytes(frame, quality=85):
    """
    Converts a numpy frame to JPEG bytes for storage in SQLite.
    """
    if frame is None:
        return None
    
    try:
        # Encode as JPEG
        success, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if success:
            return buffer.tobytes()
    except Exception as e:
        ls.error(f"Failed to encode snapshot: {e}")
        
    return None
