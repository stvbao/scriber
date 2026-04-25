# placeholder — full GUI to be ported from Transcriber app
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scriber")
        self.setMinimumSize(1200, 700)

        label = QLabel("Scriber GUI — coming soon")
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(label)
        self.setCentralWidget(container)
