import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from .frame_reader import FrameReader
from ..utils.logger import ls

class VideoController(QObject):
    """
    Core video engine that behaves exactly like a YouTube player.
    Operates in its own thread, emitting signals to pipeline.
    """
    
    frame_ready = pyqtSignal(int, object) # frame_index, frame_numpy
    seek_reset_signal = pyqtSignal()      # emitted on seek to reset tracking
    
    def __init__(self, source=None):
        super().__init__()
        self.reader = FrameReader(source)
        self.playing = False
        self.speed = 1.0
        self.source = source
        self.current_idx = 0
        self.running = True
        self.lock = threading.Lock()
        
        # Performance control
        self.last_frame_time = 0
        self.target_fps = 30.0
        
        # Do not open reader here; wait for load()
        self.worker = threading.Thread(target=self._run_loop, daemon=True)
        self.worker.start()

    def load(self, source):
        """
        Loads new file path or camera index. Reset counts if needed.
        """
        with self.lock:
            self.source = source
            self.reader.source = source # UPDATE THE READER SOURCE
            self.reader.close()
            success = self.reader.open()
            if success:
                self.target_fps = self.reader.get_fps()
                if self.target_fps <= 0: # Camera or file error
                    self.target_fps = 30.0
                ls.info(f"Loaded source: {source} @ {self.target_fps} fps")
                
                # Emit first frame immediately on load
                ret, frame = self.reader.read()
                if ret:
                    self.frame_ready.emit(0, frame)
                    # Reset pos so play starts from 0
                    self.reader.set_pos(0)
            else:
                ls.error(f"Failed to load source: {source}")
            
            self.current_idx = 0
            # On load, also treat as seek reset
            self.seek_reset_signal.emit()

    def play(self):
        with self.lock:
            self.playing = True
            ls.info("Video player Play")

    def pause(self):
        with self.lock:
            self.playing = False
            ls.info("Video player Pause")

    def stop(self):
        with self.lock:
            self.playing = False
            self.reader.set_pos(0)
            self.current_idx = 0
            self.seek_reset_signal.emit()
            ls.info("Video player Stop")

    def seek(self, frame_index):
        """
        Resets tracking and moves to specific frame.
        """
        with self.lock:
            total = self.reader.get_total_frames()
            if 0 <= frame_index < total:
                self.reader.set_pos(frame_index)
                self.current_idx = int(frame_index)
                # RESET all tracking on seek as per rule
                self.seek_reset_signal.emit()
                ls.info(f"Seeking to frame {frame_index}")

    def set_speed(self, multiplier):
        """
        multiplier: 0.25x, 0.5x, 1x, 1.5x, 2x, 4x
        Speed multiplier controls actual frame timing, not just skipping.
        """
        with self.lock:
            self.speed = multiplier
            ls.info(f"Speed set to {multiplier}x")

    def get_fps(self):
        return self.target_fps

    def get_total_frames(self):
        return int(self.reader.get_total_frames())

    def get_current_time(self):
        if self.target_fps > 0:
            return self.current_idx / self.target_fps
        return 0.0

    def get_duration_seconds(self):
        total = self.get_total_frames()
        if self.target_fps > 0:
            return total / self.target_fps
        return 0.0

    def _run_loop(self):
        """
        Time-accurate frame delivery.
        """
        while self.running:
            if not self.playing:
                time.sleep(0.01)
                continue
                
            # Speed control: delay between frames
            # target_interval = 1 / (target_fps * speed)
            start_tick = time.time()
            
            # Read frame
            ret, frame = self.reader.read()
            if not ret:
                # Loop video or stop at end
                ls.info("End of video stream reached.")
                self.playing = False
                continue
                
            # Emit frame
            self.current_idx = int(self.reader.get_pos())
            self.frame_ready.emit(self.current_idx, frame)
            
            # Accurate timing sleep
            with self.lock:
                current_speed = self.speed
                current_target_fps = self.target_fps
                
            interval = 1.0 / (current_target_fps * current_speed) if current_target_fps > 0 else 0.033
            
            # Precise sleep (accounting for processing time)
            elapsed = time.time() - start_tick
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
            # If slower than target, just continue as fast as possible

    def close(self):
        self.running = False
        self.reader.close()
        if self.worker.is_alive():
            self.worker.join(timeout=1.0)
