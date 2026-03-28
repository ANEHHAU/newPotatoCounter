from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QSplitter
from PyQt5.QtCore import Qt
from .video_widget import VideoWidget
from .control_panel import ControlPanel
from .video_control_bar import VideoControlBar

class MainLayout(QWidget):
    """Refined layout for the factory floor dashboard."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MainContent")
        
        # We use a horizontal layout with 70/30 split using layout stretch
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Left Panel (70%): Inspection Video Feeds + Controls
        left_widget = QWidget()
        left_v_layout = QVBoxLayout(left_widget)
        left_v_layout.setContentsMargins(0, 0, 0, 0)
        left_v_layout.setSpacing(10)
        
        # Video Feeds Section
        self.video_orig = VideoWidget("RAW CAMERA FEED (PRE-OVERLAY)")
        self.video_proc = VideoWidget("PROCESSED INSPECTION FEED (DETECTION & ZONES)", is_interactive=True)
        
        left_v_layout.addWidget(self.video_orig, 1)
        left_v_layout.addWidget(self.video_proc, 1)
        
        # Control Bar
        self.playback_controls = VideoControlBar()
        left_v_layout.addWidget(self.playback_controls)
        
        # Right Panel (30%): Settings, Zone Tools, Statistics
        self.right_pane = ControlPanel()
        
        layout.addWidget(left_widget, 70)
        layout.addWidget(self.right_pane, 30)