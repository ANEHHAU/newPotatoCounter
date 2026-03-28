import os
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QSplitter
from PyQt5.QtCore import Qt, pyqtSlot

from .video_panel import VideoPanel
from .control_panel import ControlPanel
from .stats_widget import StatsWidget
from ..video.video_controller import VideoController
from ..pipeline.pipeline_runner import PipelineRunner
from ..persistence.database import DatabaseManager
from ..utils.logger import ls

class MainWindow(QMainWindow):
    """
    Root QMainWindow for the Potato QC Inspector.
    """
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle(config.get('ui', {}).get('window_title', "Potato QC Inspector"))
        self.setBaseSize(1280, 800)
        self.setStyleSheet("background-color: #121212; color: #fff;")
        
        self.db = DatabaseManager(db_path=config.get('database', {}).get('path', 'potato_qc.db'))
        self.video_ctrl = VideoController()
        self.pipeline = PipelineRunner(config)
        
        self._init_ui()
        self._connect_signals()
        
        # Initial zones sync
        self.v_panel.painter.set_persistent_zones(
            roi=self.pipeline.roi,
            define=self.pipeline.define_zone,
            line=self.pipeline.counting_line
        )
        self.pipeline.start()
        ls.info("Application initialized.")

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel (60%)
        self.v_panel = VideoPanel()
        splitter.addWidget(self.v_panel)
        
        # Right Dashboard (40%)
        dashboard = QWidget()
        dash_layout = QHBoxLayout(dashboard)
        dash_layout.setContentsMargins(5, 5, 5, 5)
        dash_layout.setSpacing(10)
        
        # Column 1 (Left of dash): Zone Tools + Preprocess
        self.ctrl_panel = ControlPanel() 
        dash_layout.addWidget(self.ctrl_panel, 1)
        
        # Column 2 (Right of dash): Mode + Stats
        self.stats_widget = StatsWidget()
        dash_layout.addWidget(self.stats_widget, 1)
        
        splitter.addWidget(dashboard)
        splitter.setStretchFactor(0, 60)
        splitter.setStretchFactor(1, 40)
        layout.addWidget(splitter)

    def _connect_signals(self):
        # Video -> Pipeline
        self.video_ctrl.frame_ready.connect(self.pipeline.add_frame)
        self.video_ctrl.seek_reset_signal.connect(self.pipeline.reset_state)
        
        # Pipeline -> UI
        self.pipeline.frame_processed.connect(self._on_frame_ready)
        self.pipeline.stats_updated.connect(self.stats_widget.update_stats)
        self.pipeline.noise_detected.connect(self.stats_widget.set_noise_display)
        
        # Video Controls
        self.v_panel.play_clicked.connect(self.video_ctrl.play)
        self.v_panel.pause_clicked.connect(self.video_ctrl.pause)
        self.v_panel.seek_clicked.connect(self.video_ctrl.seek)
        self.v_panel.speed_changed.connect(self.video_ctrl.set_speed)
        
        # Dashboard Column 1 (ctrl_panel)
        self.ctrl_panel.zone_tool_clicked.connect(self._on_zone_tool_request)
        self.ctrl_panel.preproc_params_changed.connect(self._on_preproc_changed)
        
        # Dashboard Column 2 (stats_widget)
        self.stats_widget.source_changed.connect(self._on_source_changed)
        self.stats_widget.mode_changed.connect(lambda mode: self.pipeline.classifier.set_config(mode=mode))
        
        # Zone Painter UI Feedback
        self.v_panel.painter.zone_finished.connect(self._on_zone_save)

    @pyqtSlot(str)
    def _on_source_changed(self, source):
        self.video_ctrl.load(source)
        self.stats_widget.set_stats_info(self.video_ctrl.get_fps(), 0)
        self.db.start_session(source, self.config.get('model', {}).get('path'), self.config)

    @pyqtSlot(dict)
    def _on_preproc_changed(self, params):
        self.pipeline.preprocessor.set_config(
            b=params.get('brightness'),
            c=params.get('contrast'),
            blur=params.get('blur'),
            spacing=params.get('spacing')
        )
        self.pipeline.detector.set_config(conf=params.get('confidence'))
        self.pipeline.config['pipeline']['enable_background_removal'] = params.get('bg_removal')
        self.pipeline.trigger_reprocess()

    @pyqtSlot(str)
    def _on_zone_tool_request(self, tool):
        if tool == "clear":
            self.pipeline.update_zones(roi=[], define_zone=[], counting_line=[])
            self.v_panel.painter.set_persistent_zones(roi=[], define=[], line=[])
            return
        if tool == "stop":
            self.v_panel.painter.stop_drawing()
        else:
            self.v_panel.painter.start_drawing(tool)

    @pyqtSlot(str, list)
    def _on_zone_save(self, z_type, points):
        if z_type == "roi": self.pipeline.update_zones(roi=points)
        elif z_type == "def": self.pipeline.update_zones(define_zone=points)
        elif z_type == "line": self.pipeline.update_zones(counting_line=points)
        
        self.v_panel.painter.set_persistent_zones(
            roi=self.pipeline.roi,
            define=self.pipeline.define_zone,
            line=self.pipeline.counting_line
        )

    @pyqtSlot(object, object)
    def _on_frame_ready(self, orig, proc):
        self.v_panel.set_frames(orig, proc)
        curr = self.video_ctrl.current_idx
        total = self.video_ctrl.get_total_frames()
        self.v_panel.update_timeline(curr, total, self.video_ctrl.get_fps())
        self.stats_widget.set_stats_info(self.video_ctrl.get_fps(), self.pipeline.fps_mon.fps)

    def closeEvent(self, event):
        ls.info("Closing application...")
        self.pipeline.stop()
        self.video_ctrl.close()
        self.db.end_session()
        self.db.close()
        event.accept()
