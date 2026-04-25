from __future__ import annotations
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, QTimer, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QScrollArea, QTextEdit, QFileDialog, QFrame, QSizePolicy,
    QListWidget, QTabWidget,
)

from scriber.gui.worker import Worker

# ── Data ──────────────────────────────────────────────────────────────────────

AUDIO_EXTENSIONS = {".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"}

LANGUAGES = {
    "Auto-detect": "",
    "English": "en",
    "Chinese": "zh",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Serbian": "sr",
    "Japanese": "ja",
    "Korean": "ko",
    "Arabic": "ar",
    "Turkish": "tr",
    "Hindi": "hi",
}

EXPORT_FORMATS = ["txt", "srt", "vtt", "json", "md", "html", "all"]
DEVICES        = ["auto", "mlx", "cpu", "gpu"]
MODELS         = ["large-v3-turbo", "large-v3", "large-v2", "medium", "small", "base", "tiny"]

# ── Colours ───────────────────────────────────────────────────────────────────

BG      = "#1c1c1c"
PANEL   = "#252525"
BORDER  = "#383838"
BLUE    = "#2b6cb0"
BLUE_HV = "#245a9a"
GREEN   = "#2a7d4f"
GREEN_HV= "#1f5e3a"
RED     = "#c0392b"
RED_HV  = "#922b21"
TEXT    = "#e8e8e8"
DIM     = "#888888"
MONO    = "Menlo, Monaco, Courier New"

WELCOME = (
    "<span style='color:#4fc3f7;font-size:14px;font-weight:600;'>Scriber is ready.</span><br><br>"
    "<span style='color:#aaa;'>"
    "Offline transcription for qualitative researchers.<br>"
    "Select your audio files, configure settings, then press <b>Start</b>.<br><br>"
    "Transcriptions are saved in the selected output folder."
    "</span>"
)

# ── Stylesheet ────────────────────────────────────────────────────────────────

def stylesheet():
    return f"""
    * {{ font-family: Helvetica Neue, Helvetica, Arial; font-size: 13px; color: {TEXT}; }}
    QMainWindow, QWidget {{ background: {BG}; }}

    QScrollArea {{
        border: none;
        border-right: 1px solid {BORDER};
        background: {PANEL};
    }}
    QScrollArea > QWidget > QWidget {{ background: {PANEL}; }}

    QLabel {{ background: transparent; color: {TEXT}; }}
    QLabel#dim {{ color: {DIM}; font-size: 11px; }}

    QComboBox {{
        background: {BLUE}; color: white; border: none;
        border-radius: 5px; padding: 5px 28px 5px 10px;
        min-width: 120px; font-weight: 500;
    }}
    QComboBox:hover {{ background: {BLUE_HV}; }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox::down-arrow {{
        width: 0; height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid white;
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background: #2e2e2e; color: {TEXT};
        border: 1px solid {BORDER};
        selection-background-color: {BLUE};
        outline: none; padding: 2px;
    }}

    QLineEdit {{
        background: {BG}; color: {TEXT};
        border: 1px solid {BORDER}; border-radius: 5px;
        padding: 5px 8px; min-width: 120px;
    }}
    QLineEdit:focus {{ border-color: {BLUE}; }}

    QCheckBox {{ background: transparent; }}

    QPushButton#browse {{
        background: {GREEN}; color: white; border: none;
        border-radius: 5px; padding: 5px 10px;
        font-size: 13px; font-weight: 500; min-width: 68px;
    }}
    QPushButton#browse:hover {{ background: {GREEN_HV}; }}

    QPushButton#start {{
        background: {GREEN}; color: white; border: none;
        border-radius: 7px; font-size: 15px; font-weight: 700;
        padding: 11px; letter-spacing: 0.5px;
    }}
    QPushButton#start:hover {{ background: {GREEN_HV}; }}
    QPushButton#start[stop="true"] {{ background: {RED}; }}
    QPushButton#start[stop="true"]:hover {{ background: {RED_HV}; }}

    QFrame#sep {{ background: {BORDER}; }}

    QTextEdit {{
        background: {BG}; color: {TEXT}; border: none;
        font-family: {MONO}; font-size: 12px; padding: 16px;
    }}

    QTabWidget::pane {{ border: none; background: {BG}; }}
    QTabBar::tab {{
        background: {PANEL}; color: {DIM};
        padding: 6px 16px; border: none;
        border-bottom: 2px solid transparent;
        font-size: 12px;
    }}
    QTabBar::tab:selected {{ color: {TEXT}; border-bottom: 2px solid {BLUE}; }}

    QScrollBar:vertical {{ background: transparent; width: 5px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 2px; min-height: 24px; }}
    QScrollBar::handle:vertical:hover {{ background: #555; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    """

# ── Custom checkbox ───────────────────────────────────────────────────────────

class CheckBox(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        box = QRect(2, 2, 16, 16)
        if self.isChecked():
            p.setBrush(QBrush(QColor(BLUE)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(box, 4, 4)
            pen = QPen(QColor("white"), 2, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.drawLine(5, 10, 8, 13)
            p.drawLine(8, 13, 15, 6)
        else:
            p.setBrush(QBrush(QColor(BG)))
            p.setPen(QPen(QColor(BORDER), 1.5))
            p.drawRoundedRect(box, 4, 4)
        p.end()

# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scriber")
        self.setMinimumSize(1200, 700)
        self.resize(1200, 700)
        self.worker          = None
        self._selected_files = []
        self._output_folder  = Path.home() / "Downloads"
        self._build_ui()
        self.log_box.setHtml(WELCOME)

        self._pulse_timer  = QTimer(self)
        self._pulse_timer.setInterval(500)
        self._pulse_timer.timeout.connect(self._pulse)
        self._pulse_idx    = 0
        self._pulse_active = False
        self._pulse_start  = 0.0

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(self._left_panel())
        h.addWidget(self._right_panel(), 1)

    # ── Left panel ────────────────────────────────────────────────────────────

    def _left_panel(self):
        scroll = QScrollArea()
        scroll.setFixedWidth(340)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(28, 32, 28, 28)
        v.setSpacing(0)

        title = QLabel("Scriber")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: white; letter-spacing: -0.5px;")
        sub = QLabel("Offline transcription · private · fast")
        sub.setStyleSheet(f"font-size: 11px; color: {DIM}; margin-bottom: 20px;")
        v.addWidget(title)
        v.addWidget(sub)

        tabs = QTabWidget()
        tabs.addTab(self._tab_transcribe(), "Transcribe")
        tabs.addTab(self._tab_settings(), "Settings")
        v.addWidget(tabs)
        v.addStretch()

        v.addSpacing(16)
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("start")
        self.start_btn.setMinimumHeight(46)
        self.start_btn.clicked.connect(self._toggle)
        v.addWidget(self.start_btn)

        scroll.setWidget(w)
        return scroll

    def _tab_transcribe(self):
        w = QWidget()
        grid = QGridLayout(w)
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(12)
        grid.setColumnStretch(1, 1)
        row = 0

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"color: {DIM}; font-size: 12px;")
            l.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return l

        def sep():
            nonlocal row
            line = QFrame()
            line.setObjectName("sep")
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFixedHeight(1)
            grid.addWidget(line, row, 0, 1, 2)
            row += 1

        def browse_btn(slot):
            btn = QPushButton("Browse")
            btn.setObjectName("browse")
            btn.setFixedWidth(68)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {GREEN}; color: white; border: none;
                    border-radius: 5px; padding: 5px 10px; font-size: 13px; font-weight: 600; }}
                QPushButton:hover {{ background: {GREEN_HV}; }}
            """)
            btn.clicked.connect(slot)
            return btn

        # Audio files
        grid.addWidget(lbl("Audio files:"), row, 0)
        grid.addWidget(browse_btn(self._browse_files), row, 1, Qt.AlignmentFlag.AlignLeft)
        row += 1

        self.file_list = QListWidget()
        self.file_list.setFixedHeight(72)
        self.file_list.setFrameShape(QFrame.Shape.NoFrame)
        self.file_list.setStyleSheet(f"""
            QListWidget {{ background: {PANEL}; border: 1px solid {BORDER};
                border-radius: 5px; color: {DIM}; font-size: 11px; padding: 2px; outline: none; }}
            QListWidget::item {{ padding: 3px 6px; background: {PANEL}; }}
            QListWidget::item:selected {{ background: {BLUE}; color: white; border-radius: 3px; }}
        """)
        self.file_list.addItem("No files selected")
        grid.addWidget(self.file_list, row, 0, 1, 2)
        row += 1

        # Output folder
        grid.addWidget(lbl("Output folder:"), row, 0)
        grid.addWidget(browse_btn(self._browse_output), row, 1, Qt.AlignmentFlag.AlignLeft)
        row += 1

        self.output_box = QLineEdit(str(self._output_folder))
        self.output_box.setReadOnly(True)
        self.output_box.setStyleSheet(f"""
            QLineEdit {{ background: {PANEL}; border: 1px solid {BORDER};
                border-radius: 5px; color: {DIM}; font-size: 11px; padding: 3px 6px; }}
        """)
        grid.addWidget(self.output_box, row, 0, 1, 2)
        row += 1

        sep()

        # Language
        self.language_combo = QComboBox()
        self.language_combo.addItems(list(LANGUAGES.keys()))
        self.language_combo.setCurrentText("Auto-detect")
        self.language_combo.wheelEvent = lambda e: e.ignore()
        grid.addWidget(lbl("Language:"), row, 0)
        grid.addWidget(self.language_combo, row, 1)
        row += 1

        # Model
        self.model_combo = QComboBox()
        self.model_combo.addItems(MODELS)
        self.model_combo.wheelEvent = lambda e: e.ignore()
        grid.addWidget(lbl("Model:"), row, 0)
        grid.addWidget(self.model_combo, row, 1)
        row += 1

        # Device
        self.device_combo = QComboBox()
        self.device_combo.addItems(DEVICES)
        self.device_combo.wheelEvent = lambda e: e.ignore()
        grid.addWidget(lbl("Device:"), row, 0)
        grid.addWidget(self.device_combo, row, 1)
        row += 1

        # Export
        self.export_combo = QComboBox()
        self.export_combo.addItems(EXPORT_FORMATS)
        self.export_combo.wheelEvent = lambda e: e.ignore()
        grid.addWidget(lbl("Export:"), row, 0)
        grid.addWidget(self.export_combo, row, 1)
        row += 1

        sep()

        # Speaker annotation
        sa_lbl = QLabel("Speaker annotation")
        sa_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #aaa; margin-top: 2px;")
        grid.addWidget(sa_lbl, row, 0, 1, 2)
        row += 1

        self.num_speakers_edit = QLineEdit()
        self.num_speakers_edit.setPlaceholderText("0  (auto-detect)")
        grid.addWidget(lbl("Speakers:"), row, 0)
        grid.addWidget(self.num_speakers_edit, row, 1)
        row += 1

        grid.setRowStretch(row, 1)
        return w

    def _tab_settings(self):
        w = QWidget()
        grid = QGridLayout(w)
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(12)
        grid.setColumnStretch(1, 1)
        row = 0

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"color: {DIM}; font-size: 12px;")
            l.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return l

        # HF Token
        hf_title = QLabel("HuggingFace token")
        hf_title.setStyleSheet("font-size: 11px; font-weight: 600; color: #aaa; margin-top: 2px;")
        grid.addWidget(hf_title, row, 0, 1, 2)
        row += 1

        hf_note = QLabel("Required for speaker annotation only.\nGet a free token at huggingface.co/settings/tokens")
        hf_note.setStyleSheet(f"color: {DIM}; font-size: 11px;")
        hf_note.setWordWrap(True)
        grid.addWidget(hf_note, row, 0, 1, 2)
        row += 1

        self.hf_token_edit = QLineEdit()
        self.hf_token_edit.setPlaceholderText("hf_...")
        self.hf_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        grid.addWidget(lbl("HF token:"), row, 0)
        grid.addWidget(self.hf_token_edit, row, 1)
        row += 1

        grid.setRowStretch(row, 1)
        return w

    # ── Right panel ───────────────────────────────────────────────────────────

    def _right_panel(self):
        wrapper = QWidget()
        wrapper.setStyleSheet(f"background: {BG};")
        v = QVBoxLayout(wrapper)
        v.setContentsMargins(20, 20, 20, 20)

        tab = QLabel("Log")
        tab.setStyleSheet(f"""
            background: {BORDER}; color: {TEXT};
            font-size: 12px; font-weight: 600;
            padding: 4px 14px; border-radius: 4px;
        """)
        tab.setFixedHeight(26)
        tab.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        v.addWidget(tab)
        v.addSpacing(6)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet(f"""
            QTextEdit {{
                background: {PANEL}; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 8px;
                font-family: {MONO}; font-size: 12px; padding: 14px;
            }}
        """)
        v.addWidget(self.log_box)
        return wrapper

    # ── Actions ───────────────────────────────────────────────────────────────

    def _browse_files(self):
        exts = " ".join(f"*{e}" for e in sorted(AUDIO_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(self, "Select audio files", "", f"Audio files ({exts})")
        if files:
            self._selected_files = [Path(f) for f in files]
            self.file_list.clear()
            self.file_list.setStyleSheet(
                self.file_list.styleSheet().replace(f"color: {DIM};", f"color: {TEXT};")
            )
            for f in files:
                self.file_list.addItem(Path(f).name)

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select output folder", str(self._output_folder))
        if folder:
            self._output_folder = Path(folder)
            self.output_box.setText(folder)
            self.output_box.setStyleSheet(
                self.output_box.styleSheet().replace(f"color: {DIM};", f"color: {TEXT};")
            )

    def _toggle(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self._set_btn_start()
        else:
            self._start()

    def _start(self):
        if not self._selected_files:
            self._log("Please select audio files first.")
            return

        try:
            num_speakers = int(self.num_speakers_edit.text().strip() or 0)
        except ValueError:
            num_speakers = 0

        config = {
            "files":         self._selected_files,
            "output_folder": self._output_folder,
            "language":      LANGUAGES[self.language_combo.currentText()],
            "device":        self.device_combo.currentText(),
            "export":        self.export_combo.currentText(),
            "model":         self.model_combo.currentText(),
            "hf_token":      self.hf_token_edit.text().strip() or None,
            "num_speakers":  num_speakers,
        }

        self.log_box.append("")
        self._pulse_active = False
        self._pulse_idx    = 0
        self._pulse_start  = 0.0
        self.worker = Worker(config)
        self.worker.log.connect(self._log)
        self.worker.log_replace.connect(self._log_replace)
        self.worker.done.connect(self._on_done)
        self.worker.start()

        self.start_btn.setText("Stop")
        self.start_btn.setProperty("stop", True)
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self._pulse_timer.start()

    def _on_done(self):
        self._pulse_timer.stop()
        self._set_btn_start()

    def _set_btn_start(self):
        self._pulse_timer.stop()
        self.start_btn.setText("Start")
        self.start_btn.setProperty("stop", False)
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

    def _pulse(self):
        if not (self.worker and self.worker.isRunning()):
            return

        import time
        if not self._pulse_active:
            self._pulse_start = time.perf_counter()

        elapsed  = time.perf_counter() - self._pulse_start
        m, s     = divmod(int(elapsed), 60)
        elapsed_str = f"{m}m {s:02d}s" if m else f"{s}s"

        # Sweeping block bar (10 chars wide, indeterminate)
        pos    = self._pulse_idx % 10
        bar    = "░" * 10
        bar    = bar[:pos] + "█" + bar[pos + 1:]
        self._pulse_idx += 1

        ts   = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  [{bar}]  {elapsed_str} elapsed"

        cursor = self.log_box.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        if self._pulse_active:
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.insertText(line)
        else:
            self.log_box.append(line)
            self._pulse_active = True
        self.log_box.setTextCursor(cursor)
        self.log_box.ensureCursorVisible()

    def _log(self, msg: str):
        self._pulse_active = False
        self._pulse_timer.start()  # resume pulse after download finishes
        ts   = datetime.now().strftime("%H:%M:%S")
        text = f"\n[{ts}] {msg.lstrip()}" if msg.startswith("\n") else f"[{ts}] {msg}"
        self.log_box.append(text)
        self.log_box.ensureCursorVisible()

    def _log_replace(self, msg: str):
        """Overwrite the last line — used for download progress updates."""
        self._pulse_timer.stop()   # pause pulse while download is active
        self._pulse_active = False
        ts     = datetime.now().strftime("%H:%M:%S")
        text   = f"[{ts}] {msg}"
        cursor = self.log_box.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.select(cursor.SelectionType.LineUnderCursor)
        cursor.insertText(text)
        self.log_box.setTextCursor(cursor)
        self.log_box.ensureCursorVisible()
