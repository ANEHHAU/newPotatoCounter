import sys
import os
from PyQt5.QtWidgets import QApplication
from app.main_window import MainWindow

# Add current directory to path so app can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("PotatoCounter")
    
    # Optional: Splash screen could go here
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
