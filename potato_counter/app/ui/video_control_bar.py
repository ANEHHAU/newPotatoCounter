from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QSlider, QLabel, 
                             QComboBox, QSizePolicy, QStyle, QFrame, QVBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTime
from PyQt5.QtGui import QIcon

class VideoControlBar(QFrame):
    """YouTube-style playback control bar with HH:MM:SS and Speed buttons."""
    play_toggled = pyqtSignal()
    seek_requested = pyqtSignal(int)
    speed_changed = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("VideoControlBar")
        self.setFixedHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(5)
        
        # 1. Progress Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.sliderMoved.connect(self.seek_requested.emit)
        layout.addWidget(self.slider)

        # 2. Control Row
        controls = QHBoxLayout()
        controls.setSpacing(10)
        
        # Play/Pause
        self.btn_play = QPushButton()
        self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btn_play.setFixedSize(50, 50)
        self.btn_play.setStyleSheet("background: transparent; border-radius: 25px;")
        self.btn_play.clicked.connect(self.play_toggled.emit)
        controls.addWidget(self.btn_play)
        
        # Time display (HH:MM:SS)
        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setStyleSheet("color: #b0b0b0; font-family: 'Consolas'; font-size: 14px;")
        controls.addWidget(self.time_label)
        
        controls.addStretch()
        
        # Speed buttons stack
        controls.addWidget(QLabel("SPEED:"))
        self.btn_group = QHBoxLayout()
        self.speeds = [0.25, 0.5, 1.0, 2.0, 4.0]
        self.speed_buttons = []
        for s in self.speeds:
            btn = QPushButton(f"{s}x")
            btn.setFixedSize(60, 30)
            btn.setCheckable(True)
            if s == 1.0: btn.setChecked(True)
            btn.clicked.connect(lambda checked, val=s: self._on_speed_click(val))
            controls.addWidget(btn)
            self.speed_buttons.append(btn)
        
        controls.addSpacing(20)
        
        # FPS display
        self.fps_label = QLabel("IN: 0.0 FPS | PROC: 0.0 FPS")
        self.fps_label.setStyleSheet("color: #00c853; font-weight: bold;")
        controls.addWidget(self.fps_label)
        
        layout.addLayout(controls)

    def _on_speed_click(self, val):
        for btn in self.speed_buttons:
            btn.setChecked(btn.text() == f"{val}x")
        self.speed_changed.emit(val)

    def set_duration(self, frames: int):
        self.slider.setRange(0, max(0, frames))

    def update_position(self, frame_idx: int, total_frames: int, fps: float):
        if total_frames > 0:
            self.slider.setValue(frame_idx)
            # Use HH:MM:SS
            cur_sec = int(frame_idx / fps) if fps > 0 else 0
            tot_sec = int(total_frames / fps) if fps > 0 else 0
            
            def fmt_time(s):
                h = s // 3600
                m = (s % 3600) // 60
                sec = s % 60
                return f"{h:02d}:{m:02d}:{sec:02d}"
            
            self.time_label.setText(f"{fmt_time(cur_sec)} / {fmt_time(tot_sec)}")
        else:
            self.time_label.setText("LIVE / STREAM")

    def set_playback_state(self, playing: bool):
        if playing:
            self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))