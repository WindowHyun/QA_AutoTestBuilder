from gui.qt_app import AutoTestAppQt
from PySide6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoTestAppQt()
    window.show()
    sys.exit(app.exec())