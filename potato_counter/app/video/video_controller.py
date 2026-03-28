from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QObject
import time
import numpy as np
from typing import Optional, List
from .frame_reader import FrameReader
from .fps_monitor import FPSMonitor
from ..pipeline.processor import PipelineProcessor
from ..pipeline.events import ProcessingResults
from ..utils.config_loader import PotatoCounterConfig

class VideoController(QThread):
    """Main video loop with speed scaling and synchronization."""
    new_results = pyqtSignal(object) # ProcessingResults
    status_changed = pyqtSignal(str) # "playing", "paused", "finished"
    pipeline_reset_requested = pyqtSignal()
    
    def __init__(self, config: PotatoCounterConfig):
        super().__init__()
        self.config = config
        self.reader = FrameReader(config.video.source)
        self.processor = PipelineProcessor(config)
        self.fps_monitor = FPSMonitor()
        
        # Internal state
        self._running = False
        self._paused = True
        self._speed_multiplier = 1.0
        self._target_fps = 30.0
        
        self.current_frame_idx = 0
        self.total_frames = 0
        self.is_camera = False

    def load_source(self, source: str):
        """Changes the video source and resets state."""
        self.reader.source = source
        if self.reader.open():
            self.total_frames = self.reader.total_frames
            self.is_camera = self.reader.is_camera
            self._target_fps = self.reader.fps
            self.current_frame_idx = 0
            self.pipeline_reset_requested.emit()
            self.processor.reset()
            return True
        return False

    def set_speed(self, multiplier: float):
        """Scales video delay and simulated conveyor speed."""
        self._speed_multiplier = multiplier
        # Seeking/Speed change resets tracks per requirement
        self.pipeline_reset_requested.emit()
        self.processor.reset()

    def seek_to_frame(self, frame_idx: int):
        """Repositional navigation with track reset."""
        if not self.is_camera:
            self.reader.set_frame_index(frame_idx)
            self.current_frame_idx = frame_idx
            self.pipeline_reset_requested.emit()
            self.processor.reset()
            if self._paused:
                self.process_single_step()

    def toggle_play(self):
        self._paused = not self._paused
        self.status_changed.emit("playing" if not self._paused else "paused")

    def run(self):
        self._running = True
        while self._running:
            if self._paused:
                time.sleep(0.01)
                continue
            
            # Use precise timing based on target FPS and multiplier
            delay = 1.0 / (self._target_fps * self._speed_multiplier) if self._speed_multiplier > 0 else 0.1
            t_start = time.time()
            
            success, frame = self.reader.read()
            if not success:
                if not self.is_camera:
                    self._paused = True
                    self.status_changed.emit("finished")
                    self.current_frame_idx = 0
                    self.reader.set_frame_index(0)
                continue
            
            self.current_frame_idx = self.reader.get_frame_index()
            self.fps_monitor.tick()
            
            # 3. Process Frame
            results = self.processor.process_frame(frame, time.time(), self.fps_monitor.get_fps())
            if results:
                self.new_results.emit(results)
            
            # Wait for remaining duration of frame
            elapsed = time.time() - t_start
            if elapsed < delay:
                time.sleep(delay - elapsed)
                
        self.reader.close()

    def process_single_step(self):
        """Single frame render for manual seek/pause preview."""
        success, frame = self.reader.read()
        if success:
            results = self.processor.process_frame(frame, time.time(), 0)
            if results: self.new_results.emit(results)
            if not self.is_camera:
                self.reader.set_frame_index(self.current_frame_idx)

    def set_config(self, config: PotatoCounterConfig):
        self.config = config
        self.processor.set_config(config)

    def stop(self):
        self._running = False
        self.wait()
