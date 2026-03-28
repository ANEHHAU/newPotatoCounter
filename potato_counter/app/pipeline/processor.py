import cv2
import numpy as np
import time
from typing import List, Optional, Tuple
from ..services.mock_detection_service import MockDetectionService
from ..services.tracking_service import TrackingService
from ..services.counting_service import CountingService
from ..utils.config_loader import PotatoCounterConfig
from ..pipeline.state_machine import PotatoStateMachine
from ..pipeline.events import ProcessingResults

class PipelineProcessor:
    """Orchestrates detection, tracking, zone analysis, and counting for each frame."""
    def __init__(self, config: PotatoCounterConfig):
        self.config = config
        self.detector = MockDetectionService(config.pipeline.confidence_threshold)
        self.tracker = TrackingService(config.pipeline.iou_threshold)
        self.counter = CountingService()
        self.state_machine = PotatoStateMachine(config.zones.roi, config.zones.define_zone, config.operating_mode)
        
        # Track pipeline timings
        self._last_time = time.time()
        self.processing_fps = 0.0

    def process_frame(self, frame: np.ndarray, timestamp: float, input_fps: float) -> Optional[ProcessingResults]:
        """Runs the entire pipeline on a single frame."""
        t_start = time.time()
        
        # 1. Preprocess (simulated logic for now, using config parameters)
        processed_frame = self._preprocess(frame)

        # 2. Mock Detection
        detections = self.detector.detect(frame, self.config.operating_mode)

        # 3. Tracking
        tracks = self.tracker.update(detections, self.config.zones.roi)

        # 4. State Transitions (Zone Logic)
        for track in tracks:
            self.state_machine.update_track(track)

        # 5. Counting (Line crossing)
        self.counter.update(tracks, self.config.zones.count_line)

        # 6. Calculate conveyor speed and processing FPS
        t_end = time.time()
        curr_fps = 1.0 / (t_end - t_start) if (t_end - t_start) > 0 else 0
        self.processing_fps = 0.9 * self.processing_fps + 0.1 * curr_fps # EMA filter
        
        # Estimate speed (px/s)
        speeds = []
        for track in tracks:
            if len(track.history) >= 2:
                dist = np.linalg.norm(np.array(track.history[-1]) - np.array(track.history[-2]))
                speeds.append(dist * input_fps)
        conveyor_speed = np.mean(speeds) if speeds else 0.0

        # 7. Render (overlay all data)
        visualization_frame = self._draw_overlays(processed_frame.copy(), tracks)

        return ProcessingResults(
            original_frame=frame,
            processed_frame=visualization_frame,
            tracks=tracks,
            stats=self.counter.stats,
            fps=self.processing_fps,
            input_fps=input_fps,
            conveyor_speed=float(conveyor_speed),
            timestamp=timestamp
        )

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Apply brightness, contrast, and CLAHE as per config."""
        # 1. Brightness and Contrast
        alpha = (self.config.pipeline.contrast + 100) / 100.0
        beta = self.config.pipeline.brightness
        processed = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
        
        # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        if self.config.pipeline.clahe_clip_limit > 0:
            lab = cv2.cvtColor(processed, cv2.COLOR_BGR2LAB)
            l, a, b_chan = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=self.config.pipeline.clahe_clip_limit, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b_chan))
            processed = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
            
        # 3. Background Removal (Otsu) - Just for demo visual
        if self.config.pipeline.enable_otsu:
            gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            # Create a white background for non-masked area or just black 
            # Per requirement: "Bottom half: Processed video (with ROI white background, overlays...)"
            # This is complex, let's do simply: remove background.
            processed = cv2.bitwise_and(processed, processed, mask=mask)
            # To make background white
            processed[mask == 0] = [255, 255, 255]

        return processed

    def _draw_overlays(self, frame, tracks) -> np.ndarray:
        """Visualizes ROI, zones, and tracks on the frame."""
        # 1. ROI
        if self.config.zones.roi:
            roi_np = np.array(self.config.zones.roi, dtype=np.int32)
            cv2.polylines(frame, [roi_np], True, (0, 255, 0), 2)
            
        # 2. Define Zone
        if self.config.zones.define_zone:
            def_zone_np = np.array(self.config.zones.define_zone, dtype=np.int32)
            cv2.polylines(frame, [def_zone_np], True, (255, 0, 0), 2)
            
        # 3. Count Line
        if self.config.zones.count_line:
            p1, p2 = self.config.zones.count_line[:2]
            cv2.line(frame, tuple(p1), tuple(p2), (0, 0, 255), 3)

        # 4. Tracks
        for track in tracks:
            x, y, w, h = [int(v) for v in track.bbox]
            color = (0, 255, 255) # Default yellow
            
            # Change color based on completion state/finalized classification
            label = f"ID: {track.track_id}"
            
            if track.quality.is_final:
                label += f" | {track.quality.class_name.name} ({track.quality.confidence:.2f})"
                color = (0, 255, 0) # Green for finalized
            else:
                label += " | DEFINING" if track.state.name == "DEFINING" else " | TRACKING"
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
        return frame

    def set_config(self, config: PotatoCounterConfig):
        self.config = config
        self.state_machine.roi = config.zones.roi
        self.state_machine.define_zone = config.zones.define_zone
        self.state_machine.operating_mode = config.operating_mode
        self.detector.conf_threshold = config.pipeline.confidence_threshold

    def reset(self):
        """Resets the pipeline (e.g. on seek)."""
        self.tracker.clear()
        self.counter.reset()
        # Should we reset stats too? Usually on seek we might want to reset tracking info.
