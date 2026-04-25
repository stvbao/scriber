def run_app():
    from PyQt6.QtWidgets import QApplication
    from scriber.gui.main_window import MainWindow, stylesheet
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName("Scriber")
    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
