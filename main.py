import cv2
import sys
import os
import argparse
from PyQt5.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.utils.config_loader import load_config
from app.utils.logger import ls

def main():
    # Parse CLI if needed
    parser = argparse.ArgumentParser(description="Potato QC Industrial Inspector")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()
    
    # Load Configuration
    config_path = os.path.abspath(args.config)
    config = load_config(config_path)
    
    # Set app environment
    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    # Start PyQt5 App
    app = QApplication(sys.argv)
    app.setApplicationName("Potato QC Inspector")
    
    # Check if model exists
    model_path = config.get('model', {}).get('path', '')
    if not os.path.exists(model_path):
        ls.error(f"FATAL: Model weights missing at {model_path}. Please check config.yaml")
        # In a real app we might show a picker, but for now we follow PART 12 behavior:
        # Show error dialog (simple QMessageBox or just log)
        
    window = MainWindow(config)
    window.showMaximized()
    
    ls.info("Application loop started.")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
