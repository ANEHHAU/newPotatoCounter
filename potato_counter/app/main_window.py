from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QMessageBox, QApplication
from PyQt5.QtCore import Qt, QPoint, QTimer
from .ui.video_widget import VideoWidget
from .ui.control_panel import ControlPanel
from .ui.video_control_bar import VideoControlBar
from .ui.main_layout import MainLayout
from .ui.styles import DARK_INDUSTRIAL_STYLE
from .video.video_controller import VideoController
from .utils.config_loader import load_config, save_config, PotatoCounterConfig
import os

class MainWindow(QMainWindow):
    """Refined Main Application Window for the Potato Inspection Dashboard."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PotatoCounter Industrial Dashboard")
        self.resize(1920, 1080)
        
        # 1. Load Config & Style
        self.config = load_config()
        self.setStyleSheet(DARK_INDUSTRIAL_STYLE)
        
        # 2. Layout & Shortcuts
        self.ui_layout = MainLayout(self)
        self.setCentralWidget(self.ui_layout)
        
        self.video_orig = self.ui_layout.video_orig
        self.video_proc = self.ui_layout.video_proc
        self.playback_controls = self.ui_layout.playback_controls
        self.right_pane = self.ui_layout.right_pane
        
        # 3. Core Engine
        self.controller = VideoController(self.config)
        
        # 4. Local App State
        self.active_drawing_mode = None 
        self.temp_drawing_points = []
        self._is_fullscreen = False

        self._connect_signals()
        
        # Auto-init dashboard state
        self._on_source_change_default()

    def _connect_signals(self):
        # Video Processor Logic
        self.controller.new_results.connect(self._on_frame_processed)
        self.controller.status_changed.connect(self._on_status_changed)
        
        # Playback & Speed Controls
        self.playback_controls.play_toggled.connect(self.controller.toggle_play)
        self.playback_controls.seek_requested.connect(self.controller.seek_to_frame)
        self.playback_controls.speed_changed.connect(self.controller.set_speed)
        
        # Sidebar Controls
        self.right_pane.btn_open.clicked.connect(self._select_video_file)
        self.right_pane.btn_camera.clicked.connect(lambda: self._on_source_change("0"))
        self.right_pane.config_changed.connect(self._sync_processor_config)
        self.right_pane.zone_tool_activated.connect(self._handle_zone_tool)
        
        # Processed Video Interactions (Drawing)
        self.video_proc.mouse_clicked.connect(self._on_video_click)

    def keyPressEvent(self, event):
        """User interaction shortcuts (F11 for Full Screen)."""
        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_Escape:
            if self.active_drawing_mode:
                self._handle_zone_tool(self.active_drawing_mode) # Finish drawing
            elif self._is_fullscreen:
                self.toggle_fullscreen()
        super().keyPressEvent(event)

    def toggle_fullscreen(self):
        self._is_fullscreen = not self._is_fullscreen
        if self._is_fullscreen:
            self.showFullScreen()
        else:
            self.showNormal()

    def _on_frame_processed(self, results):
        # 1. Update Video Panels
        self.video_orig.update_frame(results.original_frame)
        self.video_proc.update_frame(results.processed_frame)
        
        # 2. Update Playback Bar (HH:MM:SS)
        self.playback_controls.update_position(
            self.controller.current_frame_idx, 
            self.controller.total_frames,
            self.controller._target_fps
        )
        self.playback_controls.update_fps(results.input_fps, results.fps)
        
        # 3. Update Statistics & Info
        self.right_pane.update_stats(results.stats, self.config.operating_mode, results.conveyor_speed)
        self.right_pane.info_text.setText(
            f"STATUS: {'PLAYING' if not self.controller._paused else 'PAUSED'}\n"
            f"SOURCE: {'CAMERA' if self.controller.is_camera else 'VIDEO FILE'}\n"
            f"RESOLUTION: {results.original_frame.shape[1]}x{results.original_frame.shape[0]}"
        )

    def _on_status_changed(self, status):
        self.playback_controls.set_playback_state(status == "playing")

    def _on_source_change_default(self):
        # Try to open default camera or last used source
        self._on_source_change(self.config.video.source or "0")

    def _select_video_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Videos (*.mp4 *.avi *.mov *.mkv)")
        if file_name:
            self._on_source_change(file_name)

    def _on_source_change(self, source):
        if self.controller.load_source(source):
            self.config.video.source = source
            self.playback_controls.set_duration(self.controller.total_frames)
            self.controller.start()
            self.controller.pause()
            save_config(self.config)

    def _handle_zone_tool(self, tool_type):
        """Handles the toggle between 'SET' and 'FINISH' logic."""
        if tool_type == "CLEAR":
            self.config.zones.roi = []
            self.config.zones.define_zone = []
            self.config.zones.count_line = None
            self._sync_processor_config()
            save_config(self.config)
            return

        if self.active_drawing_mode == tool_type:
            # FINISH was clicked
            self._finalize_zone_drawing()
        else:
            # START drawing mode
            self.active_drawing_mode = tool_type
            self.temp_drawing_points = []
            self.video_proc.drawing_points = [] # Clear widget temp points
            self.video_proc.set_interaction(True)
            self.right_pane.set_zone_btn_state(tool_type, True)

    def _on_video_click(self, point: QPoint):
        if not self.active_drawing_mode:
            return
            
        p = [point.x(), point.y()]
        self.temp_drawing_points.append(p)
        
        # Visual cues for drawing are handled inside VideoWidget via its mouse events 
        # But we can also auto-finalize for lines
        if self.active_drawing_mode == "LINE" and len(self.temp_drawing_points) == 2:
            self._finalize_zone_drawing()

    def _finalize_zone_drawing(self):
        if not self.active_drawing_mode:
            return
            
        if self.active_drawing_mode == "ROI":
            self.config.zones.roi = self.temp_drawing_points
        elif self.active_drawing_mode == "DEFINE":
            self.config.zones.define_zone = self.temp_drawing_points
        elif self.active_drawing_mode == "LINE" and len(self.temp_drawing_points) >= 2:
            self.config.zones.count_line = self.temp_drawing_points[:2]

        # Reset UI interaction
        self.right_pane.set_zone_btn_state(self.active_drawing_mode, False)
        self.video_proc.set_interaction(False)
        self.active_drawing_mode = None
        self.temp_drawing_points = []
        
        self._sync_processor_config()
        save_config(self.config)

    def _sync_processor_config(self):
        """Maps sidebar slider/dropdown values to the running processor config."""
        self.config.operating_mode = self.right_pane.mode_combo.currentIndex() + 1
        self.config.pipeline.brightness = self.right_pane.brightness_slider.value()
        self.config.pipeline.contrast = self.right_pane.contrast_slider.value()
        self.config.pipeline.clahe_clip_limit = self.right_pane.clahe_slider.value() / 10.0
        self.config.pipeline.confidence_threshold = self.right_pane.conf_slider.value() / 100.0
        self.config.pipeline.enable_otsu = self.right_pane.otsu_check.isChecked()
        self.config.video.processing_fps_limit = int(self.right_pane.fps_combo.currentText())
        
        self.controller.set_config(self.config)

    def closeEvent(self, event):
        self.controller.stop()
        save_config(self.config)
        event.accept()