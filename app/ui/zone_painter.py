from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QPolygonF
from ..utils.logger import ls

class ZonePainter(QWidget):
    """
    Mouse-driven ROI/zone drawing and persistent rendering overlay.
    """
    zone_finished = pyqtSignal(str, list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.current_zone_type = None
        self.drawing = False
        self.points = [] 
        
        # Persistent zones for display before/during video
        self.roi_pts = []
        self.def_pts = []
        self.line_pts = []
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def set_persistent_zones(self, roi=None, define=None, line=None):
        """
        Updates the permanent visual markers.
        """
        if roi is not None: self.roi_pts = [QPointF(p[0], p[1]) for p in roi]
        if define is not None: self.def_pts = [QPointF(p[0], p[1]) for p in define]
        if line is not None: self.line_pts = [QPointF(p[0], p[1]) for p in line]
        self.update()

    def start_drawing(self, zone_type):
        self.current_zone_type = zone_type
        self.drawing = True
        self.points = []
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.update()

    def stop_drawing(self):
        if not self.drawing: return
        
        normalized = [[p.x(), p.y()] for p in self.points]
        
        # Immediate local update for instant feedback
        if self.current_zone_type == "roi": self.roi_pts = list(self.points)
        elif self.current_zone_type == "def": self.def_pts = list(self.points)
        elif self.current_zone_type == "line": self.line_pts = list(self.points)
        
        self.zone_finished.emit(self.current_zone_type, normalized)
        
        self.drawing = False
        self.current_zone_type = None
        self.points = []
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.update()

    def mousePressEvent(self, event):
        if not self.drawing: return
        
        nx = event.x() / self.width()
        ny = event.y() / self.height()
        self.points.append(QPointF(nx, ny))
        
        # Counting line: exactly 2 points
        if self.current_zone_type == "line" and len(self.points) >= 2:
            self.stop_drawing()
        
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Draw Persistent Zones
        self._draw_pts(painter, self.roi_pts, QColor(0, 255, 0), "ROI", False)
        self._draw_pts(painter, self.def_pts, QColor(0, 100, 255, 100), "DEFINE ZONE", True)
        self._draw_pts(painter, self.line_pts, QColor(255, 0, 0), "COUNT LINE", False, is_line=True)
        
        # 2. Draw Current Drawing (Yellow)
        if self.drawing and self.points:
            color = QColor(255, 255, 0) # Yellow for active drawing
            self._draw_pts(painter, self.points, color, f"Drawing {self.current_zone_type}...", False, is_line=(self.current_zone_type=="line"))

    def _draw_pts(self, painter, pts, color, label, fill=False, is_line=False):
        if not pts: return
        
        w, h = self.width(), self.height()
        pixel_pts = [QPointF(p.x() * w, p.y() * h) for p in pts]
        
        pen = QPen(color, 2, Qt.SolidLine)
        painter.setPen(pen)
        
        if is_line and len(pixel_pts) >= 2:
            painter.drawLine(pixel_pts[0], pixel_pts[1])
        elif len(pixel_pts) > 1:
            poly = QPolygonF(pixel_pts)
            if fill:
                painter.setBrush(color)
                painter.drawPolygon(poly)
            else:
                painter.drawPolyline(poly)
                if len(pixel_pts) > 2: # Close polygon
                    painter.drawLine(pixel_pts[-1], pixel_pts[0])

        # Label
        painter.setPen(QPen(color, 2))
        painter.drawText(pixel_pts[0] + QPointF(0, -10), label)
        
        # Dots
        for pt in pixel_pts:
            painter.drawEllipse(pt, 3, 3)
