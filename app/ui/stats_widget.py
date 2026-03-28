from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QProgressBar, QPushButton, QComboBox, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal
from ..utils.logger import ls

class StatsWidget(QWidget):
    """
    Right Dashboard Column: 
    Top: Section 1 (Mode & Info)
    Bottom: Section 4 (Output Stats)
    """
    source_changed = pyqtSignal(str)   
    mode_changed = pyqtSignal(str)     
    export_requested = pyqtSignal()
    clear_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # --- SECTION 1: MODE & INFO (Top Right) ---
        s1 = QFrame(); s1.setFrameShape(QFrame.StyledPanel); s1.setStyleSheet("background: #1e1e1e;")
        s1_layout = QVBoxLayout(s1)
        lbl_s1 = QLabel("SECTION 1: MODE & INFO"); lbl_s1.setStyleSheet("color: #aaa; font-weight: bold;")
        s1_layout.addWidget(lbl_s1)
        
        btn_src = QPushButton("Select Video File")
        btn_src.clicked.connect(self._on_source_click)
        s1_layout.addWidget(btn_src)
        
        btn_cam = QPushButton("Connect Camera (Default)")
        btn_cam.clicked.connect(lambda: self.source_changed.emit("0"))
        s1_layout.addWidget(btn_cam)
        
        mode_box = QComboBox(); mode_box.addItems(["Good/Defect", "Full Class"])
        mode_box.currentTextChanged.connect(self.mode_changed.emit)
        s1_layout.addLayout(self._label_wrap("Mode:", mode_box))
        
        self.lbl_noise_est = QLabel("Predicted Noise: 0%")
        self.lbl_noise_est.setStyleSheet("color: #4df; font-weight: bold; font-size: 11px;")
        s1_layout.addWidget(self.lbl_noise_est)
        
        self.lbl_src_name = QLabel("Source: None")
        self.lbl_src_fps = QLabel("Src FPS: 0.0")
        self.lbl_proc_fps = QLabel("Proc FPS: 0.0")
        for lbl in [self.lbl_src_name, self.lbl_src_fps, self.lbl_proc_fps]:
            lbl.setStyleSheet("font-size: 10px; color: #666;")
            s1_layout.addWidget(lbl)
            
        layout.addWidget(s1)

        # --- SECTION 4: OUTPUT (Bottom Right) ---
        s4 = QFrame(); s4.setFrameShape(QFrame.StyledPanel); s4.setStyleSheet("background: #1e1e1e;")
        s4_layout = QVBoxLayout(s4)
        lbl_s4 = QLabel("SECTION 4: OUTPUT"); lbl_s4.setStyleSheet("color: #aaa; font-weight: bold;")
        s4_layout.addWidget(lbl_s4)
        
        total_row = QHBoxLayout(); total_row.addWidget(QLabel("Total:"))
        self.lbl_total = QLabel("000")
        self.lbl_total.setStyleSheet("font-weight: bold; font-size: 16px; color: #fff;")
        total_row.addWidget(self.lbl_total, 0, Qt.AlignRight)
        s4_layout.addLayout(total_row)
        
        self.bar_good = QProgressBar(); self.bar_good.setStyleSheet("QProgressBar::chunk { background-color: #0d0; }"); self.bar_good.setFormat("Good: %v")
        self.bar_defect = QProgressBar(); self.bar_defect.setStyleSheet("QProgressBar::chunk { background-color: #d00; }"); self.bar_defect.setFormat("Defect: %v")
        s4_layout.addWidget(self.bar_good); s4_layout.addWidget(self.bar_defect)
        
        self.lbl_damaged = QLabel("Damaged: 0")
        self.lbl_diseased = QLabel("Diseased: 0")
        self.lbl_sprouted = QLabel("Sprouted: 0")
        self.lbl_deformed = QLabel("Deformed: 0")
        self.lbl_unknown = QLabel("Unknown:  0")
        for lbl in [self.lbl_damaged, self.lbl_diseased, self.lbl_sprouted, self.lbl_deformed, self.lbl_unknown]:
            lbl.setStyleSheet("font-family: 'Courier New'; font-size: 11px; color: #ccc;")
            s4_layout.addWidget(lbl)
            
        self.lbl_speed = QLabel("Belt Speed: 0.00 m/s"); self.lbl_rate = QLabel("Defect Rate: 0.0%  ")
        self.lbl_speed.setStyleSheet("color: #4df; font-weight: bold;"); self.lbl_rate.setStyleSheet("color: #f80; font-weight: bold;")
        s4_layout.addWidget(self.lbl_speed); s4_layout.addWidget(self.lbl_rate)
        
        btn_layout = QHBoxLayout()
        btn_export = QPushButton("Export"); btn_export.clicked.connect(self.export_requested.emit)
        btn_clear = QPushButton("Reset"); btn_clear.clicked.connect(self.clear_requested.emit)
        btn_layout.addWidget(btn_export); btn_layout.addWidget(btn_clear)
        s4_layout.addLayout(btn_layout)
        
        layout.addWidget(s4)
        layout.addStretch()

    def set_noise_display(self, pct):
        self.lbl_noise_est.setText(f"Predicted Noise: {pct}%")

    def _label_wrap(self, text, widget):
        l = QHBoxLayout(); l.addWidget(QLabel(text)); l.addWidget(widget, 1, Qt.AlignRight)
        return l

    def _on_source_click(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Videos (*.mp4 *.avi *.mkv)")
        if path:
            self.source_changed.emit(path)
            self.lbl_src_name.setText(f"File: {path.split('/')[-1]}")

    def update_stats(self, event):
        self.lbl_total.setText(f"{event.total:03d}")
        mx = max(100, event.total); self.bar_good.setMaximum(mx); self.bar_defect.setMaximum(mx)
        self.bar_good.setValue(event.good); self.bar_defect.setValue(event.defect)
        classes = event.class_breakdown
        self.lbl_damaged.setText(f"Damaged:  {classes.get('damaged', 0)}")
        self.lbl_diseased.setText(f"Diseased: {classes.get('diseased', 0)}")
        self.lbl_sprouted.setText(f"Sprouted: {classes.get('sprouted', 0)}")
        self.lbl_deformed.setText(f"Deformed: {classes.get('deformed', 0)}")
        self.lbl_unknown.setText(f"Unknown:  {classes.get('unknown', 0)}")
        self.lbl_speed.setText(f"Speed: {event.belt_speed}")
        self.lbl_rate.setText(f"Rate: {event.defect_rate*100:.1f}%")

    def set_stats_info(self, src_fps, proc_fps):
        self.lbl_src_fps.setText(f"Src FPS: {src_fps:.1f}")
        self.lbl_proc_fps.setText(f"Proc FPS: {proc_fps:.1f}")
