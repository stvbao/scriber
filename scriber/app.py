def run_app():
    from PyQt6.QtWidgets import QApplication
    from scriber.gui.main_window import MainWindow
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName("Scriber")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
