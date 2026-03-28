import cv2
import time
import queue
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

from .preprocessor import Preprocessor
from ..services.detection_service import DetectionService
from ..services.tracking_service import TrackingService
from ..services.classification_service import ClassificationService
from ..services.counting_service import CountingService
from ..services.conveyor_speed_service import ConveyorSpeedService
from ..domain.track_manager import TrackManager
from ..domain.potato_track import PotatoState
from ..domain.events import QualityUpdateEvent
from ..utils.fps_monitor import FPSMonitor
from ..utils.logger import ls

class PipelineRunner(QThread):
    """
    Industrial pipeline: Coordinators CV stages with robust white-out and labeling.
    """
    frame_processed = pyqtSignal(object, object)
    stats_updated = pyqtSignal(object)
    noise_detected = pyqtSignal(int)             
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True
        self.mutex = QMutex()
        self.in_queue = queue.Queue(maxsize=config.get('video', {}).get('queue_max_depth', 3))
        self.preprocessor = Preprocessor(config)
        self.detector = DetectionService(
            model_path=config.get('model', {}).get('path', ''),
            confidence=config.get('model', {}).get('confidence_threshold', 0.45),
            iou=config.get('model', {}).get('iou_threshold', 0.5),
            device=config.get('model', {}).get('device', 'auto')
        )
        self.tracker_service = TrackingService()
        self.manager = TrackManager(max_lost_frames=config.get('tracking', {}).get('max_lost_frames', 30))
        self.classifier = ClassificationService(
            mode=config.get('pipeline', {}).get('mode', 'good_defect'),
            min_frames=config.get('tracking', {}).get('finalize_min_frames', 3),
            unknown_gap=config.get('tracking', {}).get('finalize_unknown_gap', 0.08)
        )
        self.counter = CountingService()
        self.speed_service = ConveyorSpeedService(
            mm_per_pixel=config.get('conveyor', {}).get('mm_per_pixel', 1.0)
        )
        self.roi = config.get('zones', {}).get('roi', [])
        self.define_zone = config.get('zones', {}).get('define_zone', [])
        self.counting_line = config.get('zones', {}).get('counting_line', [])
        self.counter.set_line(self.counting_line)
        self.fps_mon = FPSMonitor()
        self.input_fps = 0.0
        self.last_raw_frame = None
        self._reprocess_flag = False

    def add_frame(self, frame_index, frame):
        try:
            if self.in_queue.full():
                try: self.in_queue.get_nowait()
                except queue.Empty: pass
            self.in_queue.put_nowait((frame_index, frame))
        except Exception as e: ls.error(f"Queue error: {e}")

    def trigger_reprocess(self): self._reprocess_flag = True
    def reset_state(self):
        with QMutexLocker(self.mutex):
            self.manager.reset(); self.tracker_service.reset(); self.counter.reset_counts()
    def update_zones(self, roi=None, define_zone=None, counting_line=None):
        with QMutexLocker(self.mutex):
            if roi is not None: self.roi = roi
            if define_zone is not None: self.define_zone = define_zone
            if counting_line is not None: self.counting_line = counting_line; self.counter.set_line(counting_line)
        self.trigger_reprocess()

    def run(self):
        while self.running:
            try:
                is_reproc = False
                if self._reprocess_flag and self.last_raw_frame is not None:
                    frame = self.last_raw_frame.copy()
                    self._reprocess_flag = False
                    is_reproc = True
                else:
                    try:
                        frame_index, frame = self.in_queue.get(timeout=0.1)
                        self.last_raw_frame = frame.copy()
                        if frame_index % 30 == 0: self.noise_detected.emit(self.preprocessor.estimate_noise(frame))
                    except queue.Empty: continue
                
                with QMutexLocker(self.mutex):
                    local_roi, local_def, local_line = self.roi, self.define_zone, self.counting_line

                # 1. PREPROC + WHITE-OUT (HOLE FILLING ENABLED)
                enhanced = self.preprocessor.process_frame(frame)
                segment_mask = None
                
                if self.config.get('pipeline', {}).get('enable_background_removal', False):
                    # Robust hole-filled whitening correctly implemented here
                    rendered, segment_mask = self.preprocessor.get_bg_subtracted(enhanced)
                    
                    # Also white out anything outside ROI
                    if local_roi and len(local_roi) > 2:
                        h, w = frame.shape[:2]
                        roi_poly = (np.array(local_roi) * [w, h]).astype(np.int32)
                        roi_m = np.zeros((h, w), dtype=np.uint8)
                        cv2.fillPoly(roi_m, [roi_poly], 255)
                        rendered[roi_m == 0] = [255, 255, 255]
                else:
                    rendered = enhanced.copy()
                
                # 2. DETECTION / TRACKING
                if not is_reproc:
                    detections = self.detector.detect(enhanced)
                    if local_roi and len(local_roi) > 2:
                        h, w = frame.shape[:2]
                        roi_poly = (np.array(local_roi) * [w, h]).astype(np.int32)
                        detections = [d for d in detections if cv2.pointPolygonTest(roi_poly, 
                                     ((d['bbox'][0]+d['bbox'][2])/2, (d['bbox'][1]+d['bbox'][3])/2), False) >= 0]
                    ids, det_map = self.tracker_service.update(detections)
                    active_tracks = self.manager.update_tracks(ids, det_map)
                    
                    def_poly = (np.array(local_def) * [frame.shape[1], frame.shape[0]]).astype(np.int32) if len(local_def) > 2 else []
                    for track in active_tracks:
                        curr_box = track.bbox_history[-1]
                        is_in_def = True if len(def_poly)>0 and cv2.pointPolygonTest(def_poly, (curr_box[0]+curr_box[2])/2, (curr_box[1]+curr_box[3])/2, False)>=0 else False
                        crossed = False
                        if len(track.bbox_history) >= 2:
                            prev_box = track.bbox_history[-2]
                            p1 = [(prev_box[0]+prev_box[2])/2/frame.shape[1], (prev_box[1]+prev_box[3])/2/frame.shape[0]]
                            p2 = [(curr_box[0]+curr_box[2])/2/frame.shape[1], (curr_box[1]+curr_box[3])/2/frame.shape[0]]
                            crossed = self.counter.check_crossing(track.track_id, p1, p2)
                        track.update_state(True, is_in_def, crossed)
                        if crossed: self.counter.increment(track.final_label)
                    self.classifier.process_tracks(active_tracks)
                    self.speed_service.update(active_tracks, self.input_fps if self.input_fps > 0 else 30.0)
                else:
                    active_tracks = self.manager.get_all_active()

                # Rendering
                if segment_mask is not None:
                    # Drawing ORANGE border correctly using contours
                    contours, _ = cv2.findContours(segment_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    cv2.drawContours(rendered, contours, -1, (0, 165, 255), 1)

                self._render_overlays(rendered, active_tracks, local_roi, local_def, local_line)
                self.frame_processed.emit(frame, rendered)
                
                if not is_reproc:
                    counts = self.counter.get_stats()
                    total = counts['Total']
                    dr = (counts['DEFECT'] / total) if total > 0 else 0.0
                    self.stats_updated.emit(QualityUpdateEvent(total=total, good=counts['GOOD'], defect=counts['DEFECT'],
                                                class_breakdown=counts, belt_speed=self.speed_service.speed_display,
                                                defect_rate=dr))
            except Exception as e: ls.error(f"Pipeline error: {e}")

    def _render_overlays(self, frame, tracks, roi, definit, line):
        h, w = frame.shape[:2]
        if len(roi) > 2:
            pts = (np.array(roi) * [w, h]).astype(np.int32)
            cv2.polylines(frame, [pts], True, (0, 255, 0), 1)
        if len(definit) > 2:
            pts = (np.array(definit) * [w, h]).astype(np.int32)
            overlay = frame.copy()
            cv2.fillPoly(overlay, [pts], (255, 100, 0))
            cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        if len(line) == 2:
            p1 = (int(line[0][0]*w), int(line[0][1]*h))
            p2 = (int(line[1][0]*w), int(line[1][1]*h))
            cv2.line(frame, p1, p2, (0, 0, 255), 2)
        for track in tracks:
            color = (0, 255, 255)
            if track.state == PotatoState.IN_DEFINE_ZONE: color = (255, 128, 0)
            if track.state == PotatoState.FINALIZED: color = (0, 255, 0) if track.final_label=="GOOD" else (0,0,255)
            if track.state == PotatoState.COUNTED: color = (100, 100, 100)
            box = [int(x) for x in track.bbox_history[-1]]
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 1)
            label = f"ID:{track.track_id} {track.final_label}"
            cv2.putText(frame, label, (box[0], box[1]-8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    def stop(self): self.running = False; self.wait()
