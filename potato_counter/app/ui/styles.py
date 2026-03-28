"""Styles definition for the PotatoCounter Industrial Dashboard."""

DARK_INDUSTRIAL_STYLE = """
/* Industrial Dashboard Theme - Modern Dark */
QMainWindow, QWidget#MainContent {
    background-color: #0b0c0d;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QWidget {
    background-color: #121315;
    color: #e0e0e0;
    font-size: 15px;
}

QLabel {
    color: #b0b0b0;
    font-weight: 500;
}

QLabel#Title {
    font-size: 14px;
    font-weight: 900;
    color: #757575;
    background: transparent;
    padding: 10px 0;
}

/* GroupBox Sectioning */
QGroupBox {
    border: 1px solid #2a2c2f;
    border-radius: 8px;
    margin-top: 25px;
    padding-top: 15px;
    font-weight: bold;
    color: #4db6ac;
    background-color: #1a1c1e;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 12px;
}

/* Slider Colors */
QSlider::groove:horizontal {
    border: 1px solid #333;
    height: 6px;
    background: #252525;
    margin: 2px 0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #4db6ac;
    border: 1px solid #4db6ac;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

/* Buttons */
QPushButton {
    background-color: #2a2c2f;
    border: 1px solid #3a3c3f;
    border-radius: 4px;
    padding: 10px 15px;
    color: #ffffff;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #3a3c3f;
}

QPushButton:pressed {
    background-color: #1a1c1e;
}

/* Tool Buttons with colors */
QPushButton#BtnROI { border-left: 5px solid #00c853; }
QPushButton#BtnDefine { border-left: 5px solid #2979ff; }
QPushButton#BtnLine { border-left: 5px solid #f44336; }
QPushButton#BtnClear { background-color: #424242; }

QPushButton#FinishMode { 
    background-color: #c62828; 
    border: 2px solid #ffffff; 
}

/* Statistics Widgets */
QLabel#StatValueBig {
    font-size: 42px;
    font-weight: 900;
    color: #ffffff;
    background: transparent;
}

QLabel#StatLabel {
    font-size: 13px;
    color: #757575;
    text-transform: uppercase;
    font-weight: bold;
    background: transparent;
}

QFrame#InfoBox {
    background-color: #101010;
    border: 1px solid #333;
    border-radius: 4px;
    padding: 10px;
}

QLabel#InfoText {
    font-family: 'Consolas', monospace;
    font-size: 13px;
    color: #00c853;
}

/* Table */
QTableWidget {
    background-color: #1a1c1e;
    alternate-background-color: #121315;
    border: none;
    gridline-color: #2a2c2f;
}

QHeaderView::section {
    background-color: #2a2c2f;
    color: #b0b0b0;
    padding: 5px;
    border: none;
}

/* Control Bar */
QFrame#VideoControlBar {
    background-color: #000000;
    border-top: 1px solid #2a2c2f;
}
"""
