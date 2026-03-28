from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QHBoxLayout, QSlider, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
from ..utils.logger import ls

class ControlPanel(QWidget):
    """
    Left Dashboard Column: 
    Top: Section 3 (Zone Tools)
    Bottom: Section 2 (Preprocess Sliders)
    """
    preproc_params_changed = pyqtSignal(dict) 
    zone_tool_clicked = pyqtSignal(str) 
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # --- SECTION 3: ZONE TOOLS (Top Left) ---
        s3 = QFrame(); s3.setFrameShape(QFrame.StyledPanel); s3.setStyleSheet("background: #1e1e1e;")
        s3_layout = QVBoxLayout(s3)
        lbl_s3 = QLabel("SECTION 3: ZONE TOOLS"); lbl_s3.setStyleSheet("color: #aaa; font-weight: bold;")
        s3_layout.addWidget(lbl_s3)
        
        self.btn_roi = QPushButton("Set ROI"); self.btn_roi.setCheckable(True)
        self.btn_dfn = QPushButton("Set Define Zone"); self.btn_dfn.setCheckable(True)
        self.btn_lin = QPushButton("Set Counting Line"); self.btn_lin.setCheckable(True)
        btn_clr_zones = QPushButton("Clear All Zones")
        self.lbl_zone_status = QLabel("Status: Idle")
        
        for btn in [self.btn_roi, self.btn_dfn, self.btn_lin]:
            btn.clicked.connect(lambda checked, b=btn: self._on_zone_tool_click(b))
            s3_layout.addWidget(btn)
        
        btn_clr_zones.clicked.connect(lambda: self.zone_tool_clicked.emit("clear"))
        s3_layout.addWidget(btn_clr_zones)
        s3_layout.addWidget(self.lbl_zone_status)
        layout.addWidget(s3)
        
        # --- SECTION 2: PREPROCESS (Bottom Left) ---
        s2 = QFrame(); s2.setFrameShape(QFrame.StyledPanel); s2.setStyleSheet("background: #1e1e1e;")
        s2_layout = QVBoxLayout(s2)
        lbl_s2 = QLabel("SECTION 2: PREPROCESS"); lbl_s2.setStyleSheet("color: #aaa; font-weight: bold;")
        s2_layout.addWidget(lbl_s2)
        
        self.sl_br = self._create_slider(-50, 50, 0)
        self.sl_co = self._create_slider(0, 200, 100) 
        self.sl_bl = self._create_slider(0, 10, 0)
        self.sl_sp = self._create_slider(0, 30, 5) 
        self.sl_cf = self._create_slider(0, 100, 45) 
        
        s2_layout.addLayout(self._label_wrap("Brightness:", self.sl_br))
        s2_layout.addLayout(self._label_wrap("Contrast:", self.sl_co))
        s2_layout.addLayout(self._label_wrap("Denoising:", self.sl_bl))
        s2_layout.addLayout(self._label_wrap("Spacing:", self.sl_sp))
        s2_layout.addLayout(self._label_wrap("Confidence:", self.sl_cf))
        
        self.chk_bg = QCheckBox("Remove BG"); self.chk_bg.setChecked(False)
        s2_layout.addWidget(self.chk_bg)
        
        # Connect signals
        for widget in [self.sl_br, self.sl_co, self.sl_bl, self.sl_sp, self.sl_cf, self.chk_bg]:
            if isinstance(widget, QSlider):
                widget.valueChanged.connect(self._on_preprocess_change)
            else:
                widget.stateChanged.connect(self._on_preprocess_change)
                
        layout.addWidget(s2)
        layout.addStretch()

    def _on_zone_tool_click(self, btn):
        for other in [self.btn_roi, self.btn_dfn, self.btn_lin]:
            if other != btn: other.setChecked(False)
        if btn.isChecked():
            btn_type = "roi" if btn == self.btn_roi else ("def" if btn == self.btn_dfn else "line")
            self.zone_tool_clicked.emit(btn_type)
            self.lbl_zone_status.setText(f"Status: Drawing {btn_type}...")
            btn.setStyleSheet("background-color: #d22; color: #fff;")
        else:
            self.zone_tool_clicked.emit("stop")
            self.lbl_zone_status.setText("Status: Idle")
            btn.setStyleSheet("")

    def _label_wrap(self, text, widget):
        l = QHBoxLayout(); l.addWidget(QLabel(text)); l.addWidget(widget, 1, Qt.AlignRight)
        return l
        
    def _create_slider(self, min_val, max_val, curr):
        s = QSlider(Qt.Horizontal); s.setRange(min_val, max_val); s.setValue(curr); s.setFixedWidth(80)
        return s

    def _on_preprocess_change(self, val):
        params = {
            "brightness": self.sl_br.value(),
            "contrast": self.sl_co.value() / 100.0,
            "blur": self.sl_bl.value(),
            "spacing": self.sl_sp.value(),
            "confidence": self.sl_cf.value() / 100.0,
            "bg_removal": self.chk_bg.isChecked()
        }
        self.preproc_params_changed.emit(params)
