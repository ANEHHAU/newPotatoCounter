import cv2
import numpy as np
from ..utils.logger import ls

class Preprocessor:
    """
    Simplified Industrial Preprocessor (No CLAHE/Sharpen as requested).
    Focuses on Brightness, Contrast, Denoising and Convex Hull White-BG isolation.
    """
    def __init__(self, config):
        self.config = config
        self.brightness = config.get('pipeline', {}).get('brightness', 0)
        self.contrast = config.get('pipeline', {}).get('contrast', 1.0)
        self.blur_kernel = config.get('pipeline', {}).get('blur_kernel', 0)
        self.spacing = config.get('pipeline', {}).get('spacing', 5)
        
    def set_config(self, b=None, c=None, blur=None, spacing=None):
        if b is not None: self.brightness = b
        if c is not None: self.contrast = c
        if blur is not None: self.blur_kernel = blur
        if spacing is not None: self.spacing = spacing

    def process_frame(self, frame):
        if frame is None: return None
        processed = frame.copy()
        
        # 1. Brightness / Contrast
        if self.brightness != 0 or self.contrast != 1.0:
            processed = cv2.convertScaleAbs(processed, alpha=self.contrast, beta=self.brightness)
            
        # 2. Denoising
        if self.blur_kernel > 0:
            k = int(self.blur_kernel) * 2 + 1
            processed = cv2.GaussianBlur(processed, (k, k), 0)
            
        return processed

    def estimate_noise(self, frame):
        if frame is None: return 0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        return min(100, max(0, int((score / 500) * 100)))

    def get_bg_subtracted(self, frame):
        """
        Anti-Denting White-BG isolation with Convex Hull.
        """
        if frame is None: return frame, None
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # CONVEX HULL (The "Anti-Hõm" logic)
        final_iso_mask = np.zeros_like(mask)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) > 300:
                hull = cv2.convexHull(cnt)
                cv2.drawContours(final_iso_mask, [hull], -1, 255, -1)
                
        # Spacing
        if self.spacing > 0:
            kernel = np.ones((self.spacing*2+1, self.spacing*2+1), np.uint8)
            rendered_mask = cv2.dilate(final_iso_mask, kernel, iterations=1)
        else:
            rendered_mask = final_iso_mask
            
        # Final Rendering
        result = frame.copy()
        result[rendered_mask == 0] = [255, 255, 255]
        return result, rendered_mask
