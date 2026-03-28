import numpy as np
import random
from typing import List, Dict, Any

class MockDetectionService:
    """Mock detection service simulating a YOLOv8 detector."""
    def __init__(self, confidence_threshold: float = 0.5):
        self.conf_threshold = confidence_threshold
        self.next_id = 0
        self.potatoes: List[Dict[str, Any]] = [] # [{id, pos, class}, ...]

    def detect(self, frame: np.ndarray, operating_mode: int) -> List[Dict[str, Any]]:
        """Return list of detections: [{'bbox': [x, y, w, h], 'class': str, 'conf': float}]"""
        # For simplicity in mock, we'll just return a few random boxes that move down.
        # Real YOLO would run here.
        detections = []
        
        # Chance to spawn a new potato at the top
        if random.random() < 0.05:
            # Spawn near top (y=0 to 100)
            x = random.randint(200, 1600)
            y = random.randint(0, 100)
            self.potatoes.append({
                'id': self.next_id,
                'pos': [x, y],
                'class': self._get_random_class(operating_mode)
            })
            self.next_id += 1
            
        # Update existing positions (simulate conveyor speed)
        speed = 10 # pixels per frame
        remaining = []
        for p in self.potatoes:
            p['pos'][1] += speed
            if p['pos'][1] < 1080: # Filter out those that left frame
                remaining.append(p)
                # Return as bbox
                # Width 150-250, Height 100-200
                w, h = 200, 150
                detections.append({
                    'bbox': [p['pos'][0] - w//2, p['pos'][1] - h//2, w, h],
                    'class': p['class'],
                    'conf': 0.85 + random.random() * 0.1
                })
        self.potatoes = remaining
        return detections

    def _get_random_class(self, mode: int) -> str:
        if mode == 1: # Good/Defect
            return "GOOD" if random.random() > 0.3 else "DEFECT"
        else: # Full analysis
            choices = ["GOOD", "DAMAGED", "DISEASED", "SPROUTED", "DEFORMED"]
            weights = [0.7, 0.1, 0.05, 0.05, 0.1]
            return random.choices(choices, weights=weights)[0]
