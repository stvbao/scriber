def run_app():
    from PyQt6.QtWidgets import QApplication
    from scriber.gui.icon import create_app_icon
    from scriber.gui.main_window import MainWindow, stylesheet
    import sys

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
    sys.exit(app.exec())
