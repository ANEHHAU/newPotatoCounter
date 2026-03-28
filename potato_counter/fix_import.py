import os

def fix_pyqt_imports(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_import = '''from PyQt5.QtWidgets import (
    QWidget, QMainWindow, QApplication, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QPushButton, QComboBox, QSlider, QGroupBox, QFormLayout,
    QFrame, QSizePolicy, QScrollArea, QGridLayout, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize, QUrl
from PyQt5.QtGui import QPixmap, QImage, QIcon
'''

        # Thay thế hoặc thêm import
        if 'from PyQt5.QtWidgets' in content:
            lines = content.splitlines()
            new_lines = []
            imported = False
            for line in lines:
                if any(x in line for x in ['QtWidgets', 'QtCore', 'QtGui']) and not imported:
                    new_lines.append(new_import)
                    imported = True
                elif not any(x in line for x in ['QtWidgets', 'QtCore', 'QtGui']) or imported:
                    new_lines.append(line)
            content = '\n'.join(new_lines)
        else:
            content = new_import + '\n\n' + content

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'✓ Đã sửa import: {file_path}')
    except Exception as e:
        print(f'✗ Lỗi khi sửa {file_path}: {e}')

# Danh sách file cần sửa
files_to_fix = [
    'app/ui/video_control_bar.py',
    'app/ui/main_layout.py',
    'app/ui/video_widget.py',
    'app/ui/control_panel.py',
    'app/main_window.py'
]

base_dir = os.getcwd()
for rel_path in files_to_fix:
    full_path = os.path.join(base_dir, rel_path)
    if os.path.exists(full_path):
        fix_pyqt_imports(full_path)
    else:
        print(f'Không tìm thấy file: {rel_path}')

print('\nHoàn tất sửa tất cả import PyQt5!')
input('Nhấn Enter để thoát...')