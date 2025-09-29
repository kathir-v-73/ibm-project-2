#!/usr/bin/env python3
"""
TechKey Analysis - Desktop GUI Launcher
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from gui.main_window import MainWindow


def main():
    """Main function to launch the GUI application."""
    try:
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("TechKey Analysis")
        app.setApplicationVersion("1.0.0")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()