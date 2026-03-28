from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QPushButton, QComboBox, QSlider, QCheckBox, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, 
                             QScrollArea, QFrame, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, pyqtSignal

class ControlPanel(QWidget):
    """Right-hand configuration and statistics pane."""
    config_changed = pyqtSignal()
    zone_tool_activated = pyqtSignal(str) # "ROI", "DEFINE", "LINE", "CLEAR"
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(400)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 20, 10, 10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        self.layout = QVBoxLayout(content_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(20)
        
        # 1. Mode & Info
        self._setup_mode_section()
        # 2. Preprocess Controls
        self._setup_preprocess_section()
        # 3. Zone Tools
        self._setup_zone_section()
        # 4. Statistics
        self._setup_stats_section()
        
        self.layout.addStretch()

    def _setup_mode_section(self):
        group = QGroupBox("MODE & INFO")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        h_btn = QHBoxLayout()
        self.btn_open = QPushButton("Open Video File")
        self.btn_camera = QPushButton("Start Live Camera")
        h_btn.addWidget(self.btn_open)
        h_btn.addWidget(self.btn_camera)
        layout.addLayout(h_btn)
        
        layout.addWidget(QLabel("Inspection Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Good/Defect ONLY", "Full Analysis Mode"])
        self.mode_combo.currentIndexChanged.connect(self.config_changed.emit)
        layout.addWidget(self.mode_combo)

        h_fps = QHBoxLayout()
        h_fps.addWidget(QLabel("FPS Limit:"))
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["10", "15", "30"])
        self.fps_combo.setCurrentIndex(2) # Default 30
        self.fps_combo.currentIndexChanged.connect(self.config_changed.emit)
        h_fps.addWidget(self.fps_combo)
        layout.addLayout(h_fps)

        # Info Monospace Box
        self.info_box = QFrame()
        self.info_box.setObjectName("InfoBox")
        info_layout = QVBoxLayout(self.info_box)
        self.info_text = QLabel("STATUS: STANDBY\nSOURCE: NONE\nRESOLUTION: -")
        self.info_text.setObjectName("InfoText")
        info_layout.addWidget(self.info_text)
        layout.addWidget(self.info_box)
        
        self.layout.addWidget(group)

    def _setup_preprocess_section(self):
        group = QGroupBox("PREPROCESS CONTROLS")
        layout = QVBoxLayout(group)
        
        def add_slider(name, min_v, max_v, default):
            h = QHBoxLayout()
            h.addWidget(QLabel(name))
            val_lbl = QLabel(str(default))
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_v, max_v)
            slider.setValue(default)
            slider.valueChanged.connect(lambda v: val_lbl.setText(str(v)))
            slider.valueChanged.connect(self.config_changed.emit)
            h.addWidget(slider)
            h.addWidget(val_lbl)
            layout.addLayout(h)
            return slider
            
        self.brightness_slider = add_slider("Brightness", -100, 100, 0)
        self.contrast_slider = add_slider("Contrast", -100, 100, 0)
        self.clahe_slider = add_slider("CLAHE Clip", 0, 40, 20) # 0.0 - 4.0
        self.conf_slider = add_slider("Confidence", 30, 95, 50) # 0.30 - 0.95
        
        self.otsu_check = QCheckBox("Enable Background Removal (Otsu)")
        self.otsu_check.stateChanged.connect(self.config_changed.emit)
        layout.addWidget(self.otsu_check)
        
        self.layout.addWidget(group)

    def _setup_zone_section(self):
        group = QGroupBox("ZONE TOOLS")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        self.btn_roi = QPushButton("SET ROI")
        self.btn_roi.setObjectName("BtnROI")
        self.btn_define = QPushButton("SET DEFINE ZONE")
        self.btn_define.setObjectName("BtnDefine")
        self.btn_line = QPushButton("SET COUNT LINE")
        self.btn_line.setObjectName("BtnLine")
        self.btn_clear = QPushButton("Clear All Zones")
        self.btn_clear.setObjectName("BtnClear")
        
        self.btn_roi.clicked.connect(lambda: self.zone_tool_activated.emit("ROI"))
        self.btn_define.clicked.connect(lambda: self.zone_tool_activated.emit("DEFINE"))
        self.btn_line.clicked.connect(lambda: self.zone_tool_activated.emit("LINE"))
        self.btn_clear.clicked.connect(lambda: self.zone_tool_activated.emit("CLEAR"))
        
        layout.addWidget(self.btn_roi)
        layout.addWidget(self.btn_define)
        layout.addWidget(self.btn_line)
        layout.addWidget(self.btn_clear)
        
        self.layout.addWidget(group)

    def _setup_stats_section(self):
        group = QGroupBox("OUTPUT & STATISTICS")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # Horizontal stack for Big Values
        stats_horiz = QHBoxLayout()
        
        def create_big_stat(title, color):
            v = QVBoxLayout()
            lbl = QLabel(title)
            lbl.setObjectName("StatLabel")
            val = QLabel("0")
            val.setObjectName("StatValueBig")
            if color: val.setStyleSheet(f"color: {color};")
            v.addWidget(lbl, alignment=Qt.AlignCenter)
            v.addWidget(val, alignment=Qt.AlignCenter)
            stats_horiz.addLayout(v)
            return val
            
        self.stat_total = create_big_stat("TOTAL", "#ffffff")
        self.stat_good = create_big_stat("GOOD", "#00c853")
        self.stat_defective = create_big_stat("DEFECT", "#f44336")
        
        layout.addLayout(stats_horiz)
        
        self.stats_table = QTableWidget(4, 2)
        self.stats_table.setHorizontalHeaderLabels(["Class", "Count"])
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stats_table.setFixedHeight(140)
        self.stats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        classes = ["Damaged", "Diseased", "Sprouted", "Deformed"]
        for i, cls in enumerate(classes):
            self.stats_table.setItem(i, 0, QTableWidgetItem(cls))
            self.stats_table.setItem(i, 1, QTableWidgetItem("0"))
            
        layout.addWidget(self.stats_table)
        
        self.last_potato_label = QLabel("LAST FINISHED: -")
        self.last_potato_label.setStyleSheet("color: #757575; font-size: 11px;")
        layout.addWidget(self.last_potato_label)
        
        self.speed_label = QLabel("EST. SPEED: 0 px/s")
        self.speed_label.setStyleSheet("color: #4db6ac; font-weight: bold;")
        layout.addWidget(self.speed_label)
        
        self.layout.addWidget(group)

    def update_stats(self, stats: any, operating_mode: int, conv_speed: float):
        self.stat_total.setText(str(stats.total))
        self.stat_good.setText(str(stats.good))
        self.stat_defective.setText(str(stats.defective))
        self.speed_label.setText(f"EST. SPEED: {conv_speed:.1f} px/s")
        
        if operating_mode == 2:
            self.stats_table.item(0, 1).setText(str(stats.breakdown.get("DAMAGED", 0)))
            self.stats_table.item(1, 1).setText(str(stats.breakdown.get("DISEASED", 0)))
            self.stats_table.item(2, 1).setText(str(stats.breakdown.get("SPROUTED", 0)))
            self.stats_table.item(3, 1).setText(str(stats.breakdown.get("DEFORMED", 0)))
            self.stats_table.setVisible(True)
        else:
            self.stats_table.setVisible(False)

    def set_zone_btn_state(self, mode: str, is_active: bool):
        """Changes button appearance when in drawing mode."""
        btn_map = {"ROI": self.btn_roi, "DEFINE": self.btn_define, "LINE": self.btn_line}
        for k, btn in btn_map.items():
            if k == mode and is_active:
                btn.setText("FINISH")
                btn.setObjectName("FinishMode")
            else:
                btn.setText(f"SET {k}")
                btn.setObjectName(f"Btn{k}")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()