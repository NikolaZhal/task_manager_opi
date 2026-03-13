import sys
import os

# Fix: Qt platform plugin not found on Windows
try:
    import PyQt5
    plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins", "platforms")
    if not os.path.exists(plugin_path):
        plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), "Qt", "plugins", "platforms")
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
from database import DatabaseManager
from main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    db = DatabaseManager("tasks.db")
    window = MainWindow(db)
    window.show()

    sys.exit(app.exec_())