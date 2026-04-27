import os
import sys


def run_app():
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication
    from scriber.gui.icon import create_app_icon
    from scriber.gui.main_window import MainWindow, stylesheet

    app = QApplication(sys.argv)
    app.setApplicationName("Scriber")
    app.setApplicationDisplayName("Scriber")
    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet())
    icon = create_app_icon()
    app.setWindowIcon(icon)
    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()

    auto_quit_ms = os.environ.get("SCRIBER_APP_AUTOQUIT_MS")
    if auto_quit_ms:
        try:
            QTimer.singleShot(max(0, int(auto_quit_ms)), app.quit)
        except ValueError:
            pass

    sys.exit(app.exec())
