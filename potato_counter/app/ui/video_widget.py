from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy, QFrame
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QCursor
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect
import cv2
import numpy as np
from typing import List, Optional

class VideoWidget(QFrame):
    """Component to display high-resolution video frames (original or processed)."""
    mouse_clicked = pyqtSignal(QPoint)
    mouse_moved = pyqtSignal(QPoint)
    
    def __init__(self, title: str, is_interactive: bool = False):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setObjectName("VideoDisplay")
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("Title")
        
        self.display_label = QLabel()
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.display_label.setMinimumSize(480, 270)
        self.display_label.setStyleSheet("background-color: #0b0c0d; border-radius: 4px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self.title_label)
        layout.addWidget(self.display_label)
        
        self._current_frame = None
        self._scale_w = 1.0
        self._scale_h = 1.0
        self._offset_x = 0
        self._offset_y = 0
        
        self.is_interactive = is_interactive
        self.setMouseTracking(is_interactive)
        
        # Temp points for visually drawing while interacting
        self.drawing_points: List[QPoint] = []
        self._last_mouse_pos: Optional[QPoint] = None

    def update_frame(self, frame: np.ndarray):
        """Converts OpenCV frame to QPixmap with aspect ratio management."""
        if frame is None:
            return

        self._current_frame = frame.copy()
        height, width, channel = frame.shape
        bytes_per_line = channel * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
        
        label_size = self.display_label.size()
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Update calibration for mouse coordinate mapping
        actual_w = scaled_pixmap.width()
        actual_h = scaled_pixmap.height()
        self._scale_w = width / actual_w if actual_w > 0 else 1.0
        self._scale_h = height / actual_h if actual_h > 0 else 1.0
        self._offset_x = (label_size.width() - actual_w) // 2
        self._offset_y = (label_size.height() - actual_h) // 2
        
        # If in interactive drawing mode, overlay current pending lines
        if self.is_interactive and self.drawing_points and len(self.drawing_points) > 0:
            painter = QPainter(scaled_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 0), 2, Qt.SolidLine)
            painter.setPen(pen)
            
            # Map points from frame coordinates back to scaled pixmap coordinates
            scaled_points = []
            for dp in self.drawing_points:
                sx = int(dp.x() / self._scale_w)
                sy = int(dp.y() / self._scale_h)
                scaled_points.append(QPoint(sx, sy))
                
            # Draw line segments
            for i in range(len(scaled_points) - 1):
                painter.drawLine(scaled_points[i], scaled_points[i+1])
            
            # Draw rubber band to mouse cursor if available
            if self._last_mouse_pos and scaled_points:
                # Map mouse pos back to scaled view relative to offset
                mx = self._last_mouse_pos.x() - self._offset_x
                my = self._last_mouse_pos.y() - self._offset_y
                painter.drawLine(scaled_points[-1], QPoint(mx, my))
                
            painter.end()

        self.display_label.setPixmap(scaled_pixmap)

    def set_interaction(self, active: bool):
        self.is_interactive = active
        self.setMouseTracking(active)
        if active:
            self.display_label.setCursor(QCursor(Qt.CrossCursor))
        else:
            self.display_label.setCursor(QCursor(Qt.ArrowCursor))
            self.drawing_points = []
            self._last_mouse_pos = None

    def mousePressEvent(self, event):
        if not self.is_interactive:
            return
        
        # Map to frame coordinates
        x_mapped = (event.pos().x() - self.display_label.x() - self._offset_x) * self._scale_w
        y_mapped = (event.pos().y() - self.display_label.y() - self._offset_y) * self._scale_h
        
        if self._current_frame is not None:
            h, w = self._current_frame.shape[:2]
            if 0 <= x_mapped < w and 0 <= y_mapped < h:
                p = QPoint(int(x_mapped), int(y_mapped))
                self.drawing_points.append(p)
                self.mouse_clicked.emit(p)
                # Refresh frame with pending drawing
                self.update_frame(self._current_frame)

    def mouseMoveEvent(self, event):
        if not self.is_interactive:
            return
            
        self._last_mouse_pos = event.pos()
        if self._current_frame is not None:
            self.update_frame(self._current_frame)
            
        self.mouse_moved.emit(event.pos())
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._current_frame is not None:
            self.update_frame(self._current_frame)