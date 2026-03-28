from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSlider, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QImage, QPixmap
import cv2
from ..utils.logger import ls
from .zone_painter import ZonePainter

class VideoPanel(QWidget):
    """
    Left panel: Dual video feed + YouTube player bar.
    """
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    seek_clicked = pyqtSignal(int)
    speed_changed = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 1. Original View
        self.lbl_orig = QLabel("ORIGINAL VIDEO FEED")
        self.lbl_orig.setAlignment(Qt.AlignCenter)
        self.lbl_orig.setScaledContents(True)
        self.lbl_orig.setStyleSheet("background: #000; border: 1px solid #333;")
        self.lbl_orig.setMinimumSize(320, 180)
        layout.addWidget(self.lbl_orig, 1) # STRETCH 1
        
        # 2. Processed View (with ZonePainter overlay)
        proc_container = QFrame()
        proc_container.setMinimumSize(320, 180)
        proc_layout = QVBoxLayout(proc_container)
        proc_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_proc = QLabel("PROCESSED VIDEO (Overlays)")
        self.lbl_proc.setAlignment(Qt.AlignCenter)
        self.lbl_proc.setScaledContents(True)
        self.lbl_proc.setStyleSheet("background: #000; border: 1px solid #333;")
        self.lbl_proc.setMinimumSize(320, 180)
        proc_layout.addWidget(self.lbl_proc, 1) # STRETCH 1
        
        # Add ZonePainter as child of lbl_proc (or same container)
        self.painter = ZonePainter(self.lbl_proc)
        self.painter.setGeometry(0, 0, 640, 360)
        
        layout.addWidget(proc_container, 1) # STRETCH 1
        
        # 3. YouTube Player Bar
        player_bar = QFrame()
        player_bar.setStyleSheet("background: #1e1e1e; padding: 10px; border-radius: 5px;")
        bar_layout = QVBoxLayout(player_bar)
        
        # Timeline
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderReleased.connect(self._on_seek)
        bar_layout.addWidget(self.slider)
        
        # Controls row
        ctrl_row = QHBoxLayout()
        self.btn_play = QPushButton("▶")
        self.btn_play.clicked.connect(self._toggle_play)
        
        self.lbl_time = QLabel("00:00 / 00:00")
        
        self.speed_box = QSlider(Qt.Horizontal)
        self.speed_box.setRange(0, 5) # 0=0.25, 1=0.5, 2=1.0, 3=1.5, 4=2.0, 5=4.0
        self.speed_box.setValue(2)
        self.speed_box.setFixedWidth(80)
        self.speed_box.valueChanged.connect(self._on_speed_change)
        self.lbl_speed = QLabel("Speed: 1x")
        
        ctrl_row.addWidget(self.btn_play)
        ctrl_row.addWidget(self.lbl_time)
        ctrl_row.addStretch()
        ctrl_row.addWidget(self.lbl_speed)
        ctrl_row.addWidget(self.speed_box)
        
        bar_layout.addLayout(ctrl_row)
        layout.addWidget(player_bar)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Sync painter geometry to label
        self.painter.setGeometry(self.lbl_proc.geometry())

    def _toggle_play(self):
        if self.btn_play.text() == "▶":
            self.btn_play.setText("❚❚")
            self.play_clicked.emit()
        else:
            self.btn_play.setText("▶")
            self.pause_clicked.emit()

    def _on_seek(self):
        self.seek_clicked.emit(self.slider.value())

    def _on_speed_change(self, val):
        speeds = [0.25, 0.5, 1.0, 1.5, 2.0, 4.0]
        s = speeds[val]
        self.lbl_speed.setText(f"Speed: {s}x")
        self.speed_changed.emit(s)

    def set_frames(self, orig, proc):
        """
        Updates the image labels.
        """
        if orig is not None:
            self.lbl_orig.setPixmap(self._convert_to_pixmap(orig))
        if proc is not None:
            self.lbl_proc.setPixmap(self._convert_to_pixmap(proc))

    def _convert_to_pixmap(self, frame):
        # Resize to fixed 640x360 for display
        resized = cv2.resize(frame, (640, 360))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
        return QPixmap.fromImage(qimg)

    def update_timeline(self, curr, total, fps):
        self.slider.setMaximum(total)
        self.slider.setValue(curr)
        
        curr_sec = int(curr / fps) if fps > 0 else 0
        total_sec = int(total / fps) if fps > 0 else 0
        
        self.lbl_time.setText(f"{curr_sec//60:02}:{curr_sec%60:02} / {total_sec//60:02}:{total_sec%60:02}")
