from __future__ import annotations
from pathlib import Path
from datetime import datetime
from html import escape

from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QScrollArea, QTextEdit, QFileDialog, QFrame, QSizePolicy,
    QListWidget,
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
LOG_CYAN = "#4fc3f7"
LOG_GREEN = "#79d28b"
LOG_YELLOW = "#f0c36a"
LOG_RED = "#ff7f7f"
LOG_DIM = "#9a9a9a"

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
    * {{
        font-family: Helvetica Neue, Helvetica, Arial;
        font-size: 13px;
        color: {TEXT};
    }}
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
        background: {BLUE};
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px 28px 5px 10px;
        min-width: 120px;
        font-weight: 500;
    }}
    QComboBox:hover {{ background: {BLUE_HV}; }}
    QComboBox:focus {{ outline: 2px solid #6baed6; outline-offset: 1px; border: 2px solid #6baed6; }}
    QComboBox::drop-down {{ border: none; width: 20px; background: transparent; }}
    QComboBox QAbstractItemView {{
        background: #2e2e2e;
        color: {TEXT};
        border: 1px solid {BORDER};
        selection-background-color: {BLUE};
        outline: none;
        padding: 2px;
    }}

    QLineEdit, QSpinBox {{
        background: {BG};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 5px;
        padding: 5px 8px;
        min-width: 120px;
    }}
    QLineEdit:focus, QSpinBox:focus {{ border-color: {BLUE}; }}
    QSpinBox::up-button, QSpinBox::down-button {{
        background: {BORDER}; border: none; width: 16px;
    }}

    QCheckBox {{ background: transparent; }}

    QPushButton#browse {{
        background: {GREEN};
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px 10px;
        font-size: 13px;
        font-weight: 500;
        min-width: 68px;
    }}
    QPushButton#browse:hover {{ background: {GREEN_HV}; }}

    QPushButton#start {{
        background: {GREEN};
        color: white;
        border: none;
        border-radius: 7px;
        font-size: 15px;
        font-weight: 700;
        padding: 11px;
        letter-spacing: 0.5px;
    }}
    QPushButton#start:hover {{ background: {GREEN_HV}; }}
    QPushButton#start[stop="true"] {{ background: {RED}; }}
    QPushButton#start[stop="true"]:hover {{ background: {RED_HV}; }}

    QFrame#sep {{ background: {BORDER}; }}

    QTextEdit {{
        background: {BG};
        color: {TEXT};
        border: none;
        font-family: {MONO};
        font-size: 12px;
        padding: 16px;
    }}

    QTabWidget::pane {{ border: 0px; background: {PANEL}; }}
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
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

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
        self.setMinimumSize(1000, 720)
        self.resize(1000, 720)
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
        self._replace_active = False
        self._pulse_start  = 0.0
        self._pulse_label  = ""
        self._hard_stopping = False
        self._stopping_workers = []

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

        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(12)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(0, 100)
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

        # Translate to English
        self.translate_check = CheckBox()
        self.translate_check.stateChanged.connect(self._on_translate_changed)
        grid.addWidget(lbl("Translate to English:"), row, 0)
        grid.addWidget(self.translate_check, row, 1, Qt.AlignmentFlag.AlignLeft)
        row += 1

        self.translate_warn = QLabel("⚠ large-v3 will be used (turbo does not support)")
        self.translate_warn.setObjectName("dim")
        self.translate_warn.setWordWrap(True)
        self.translate_warn.hide()
        grid.addWidget(self.translate_warn, row, 0, 1, 2)
        row += 1

        # Model
        self.model_combo = QComboBox()
        self.model_combo.addItems(MODELS)
        self.model_combo.wheelEvent = lambda e: e.ignore()
        self.model_combo.currentTextChanged.connect(self._on_translate_changed)
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
        grid.addWidget(lbl("Export Format:"), row, 0)
        grid.addWidget(self.export_combo, row, 1)
        row += 1

        # Pause markers
        self.pause_check = CheckBox()
        grid.addWidget(lbl("Mark Pauses:"), row, 0)
        grid.addWidget(self.pause_check, row, 1, Qt.AlignmentFlag.AlignLeft)
        row += 1

        sep()

        # Speaker annotation
        sa_lbl = QLabel("Speaker annotation")
        sa_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #aaa; margin-top: 2px;")
        grid.addWidget(sa_lbl, row, 0, 1, 2)
        row += 1

        self.hf_token_edit = QLineEdit()
        self.hf_token_edit.setPlaceholderText("hf_...")
        self.hf_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        grid.addWidget(lbl("HF token:"), row, 0)
        grid.addWidget(self.hf_token_edit, row, 1)
        row += 1

        self.num_speakers_edit = QLineEdit()
        self.num_speakers_edit.setPlaceholderText("0  (auto-detect)")
        grid.addWidget(lbl("Speakers:"), row, 0)
        grid.addWidget(self.num_speakers_edit, row, 1)
        row += 1

        v.addLayout(grid)
        v.addStretch()

        v.addSpacing(16)
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("start")
        self.start_btn.setMinimumHeight(46)
        self.start_btn.clicked.connect(self._toggle)
        v.addWidget(self.start_btn)

        scroll.setWidget(w)
        return scroll

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
                background: {PANEL}; color: #ffffff;
                border: 1px solid {BORDER}; border-radius: 8px;
                font-family: {MONO}; font-size: 12px; padding: 14px;
            }}
        """)
        v.addWidget(self.log_box)
        return wrapper

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_translate_changed(self):
        turbo = "turbo" in self.model_combo.currentText()
        self.translate_warn.setVisible(self.translate_check.isChecked() and turbo)

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
            self._hard_stop_worker()
        else:
            self._start()

    def _hard_stop_worker(self):
        worker = self.worker
        if not worker:
            return

        self._hard_stopping = True
        self._disconnect_worker(worker)
        self._stopping_workers.append(worker)
        worker.done.connect(lambda w=worker: self._forget_stopped_worker(w))
        self._pulse_timer.stop()
        self._pulse_active = False
        self._replace_active = False
        self._log("Stopped by user. Current file may be incomplete.")

        worker.terminate()
        self.worker = None
        self._hard_stopping = False
        self._set_btn_start()

    def _start(self):
        if not self._selected_files:
            self._log("Please select audio files first.")
            return

        try:
            num_speakers = int(self.num_speakers_edit.text().strip() or 0)
        except ValueError:
            num_speakers = 0

        config = {
            "files":           self._selected_files,
            "output_folder":   self._output_folder,
            "language":        LANGUAGES[self.language_combo.currentText()],
            "device":          self.device_combo.currentText(),
            "export":          self.export_combo.currentText(),
            "model":           self.model_combo.currentText(),
            "hf_token":        self.hf_token_edit.text().strip() or None,
            "annotate":        bool(self.hf_token_edit.text().strip()),
            "num_speakers":    num_speakers,
            "pause_markers":   self.pause_check.isChecked(),
            "pause_threshold": 2.0,
            "translate":       self.translate_check.isChecked(),
        }

        import time
        self.log_box.append("")
        self._pulse_active = False
        self._replace_active = False
        self._pulse_idx    = 0
        self._pulse_start  = time.perf_counter()  # start once, never reset
        self._pulse_label  = ""
        self._hard_stopping = False

        worker = Worker(config)
        self.worker = worker
        worker.log.connect(self._log_from_worker)
        worker.log_replace.connect(self._log_replace_from_worker)
        worker.reset_timer.connect(self._reset_pulse_timer)
        worker.suspend_pulse.connect(self._suspend_pulse)
        worker.resume_pulse.connect(self._resume_pulse)
        worker.done.connect(self._on_done)
        worker.start()

        self.start_btn.setText("Stop")
        self.start_btn.setProperty("stop", True)
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

    def _suspend_pulse(self):
        if not self._worker_signal_current():
            return
        self._pulse_timer.stop()
        self._pulse_active = False

    def _resume_pulse(self, label: str):
        if not self._worker_signal_current():
            return
        self._pulse_label = label
        self._pulse_active = False
        self._pulse_timer.start()

    def _reset_pulse_timer(self):
        if not self._worker_signal_current():
            return
        import time
        self._pulse_start  = time.perf_counter()
        self._pulse_active = False

    def _on_done(self):
        if not self._worker_signal_current():
            return
        self._pulse_timer.stop()
        self._replace_active = False
        self.worker = None
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
        elapsed  = time.perf_counter() - self._pulse_start
        m, s     = divmod(int(elapsed), 60)
        elapsed_str = f"{m}m {s:02d}s" if m else f"{s}s"

        pos  = self._pulse_idx % 5
        bar  = "○○○○○"
        bar  = bar[:pos] + "●" + bar[pos + 1:]
        self._pulse_idx += 1

        ts   = datetime.now().strftime("%H:%M:%S")
        line = self._format_activity_line(ts, self._pulse_label or "Working", f"[{bar}]", elapsed_str)

        cursor = self.log_box.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        if self._pulse_active:
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.insertHtml(line)
        else:
            self.log_box.append(line)
            self._pulse_active = True
        self._replace_active = False
        self.log_box.setTextCursor(cursor)
        self.log_box.ensureCursorVisible()

    def _log(self, msg: str):
        self._pulse_active = False
        self._replace_active = False
        ts   = datetime.now().strftime("%H:%M:%S")
        html = self._format_log_line(ts, msg)
        self.log_box.append(html)
        self.log_box.ensureCursorVisible()

    def _log_from_worker(self, msg: str):
        if self._worker_signal_current():
            self._log(msg)

    def _log_replace(self, msg: str):
        """Overwrite the last line — used for download progress updates."""
        self._pulse_timer.stop()   # pause pulse while download is active
        self._pulse_active = False
        ts     = datetime.now().strftime("%H:%M:%S")
        text   = self._format_log_line(ts, msg)
        if self._replace_active:
            cursor = self.log_box.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.insertHtml(text)
            self.log_box.setTextCursor(cursor)
        else:
            self.log_box.append(text)
            self._replace_active = True
        self.log_box.ensureCursorVisible()

    def _log_replace_from_worker(self, msg: str):
        if self._worker_signal_current():
            self._log_replace(msg)

    def _worker_signal_current(self) -> bool:
        return self.sender() is self.worker and not self._hard_stopping

    def _disconnect_worker(self, worker: Worker):
        for signal in (
            worker.log,
            worker.log_replace,
            worker.reset_timer,
            worker.suspend_pulse,
            worker.resume_pulse,
            worker.done,
        ):
            try:
                signal.disconnect()
            except TypeError:
                pass

    def _forget_stopped_worker(self, worker: Worker):
        if worker in self._stopping_workers:
            self._stopping_workers.remove(worker)
        worker.deleteLater()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self._hard_stop_worker()
        event.accept()

    def _format_log_line(self, ts: str, msg: str) -> str:
        leading_break = msg.startswith("\n")
        text = msg.lstrip("\n")
        color = self._log_color(text)
        prefix = escape(f"[{ts}] ")
        body = escape(text)
        line = f'<span style="color:{LOG_DIM};">{prefix}</span><span style="color:{color};">{body}</span>'
        return f"<br>{line}" if leading_break else line

    def _format_activity_line(self, ts: str, label: str, frame: str, elapsed: str) -> str:
        prefix = escape(f"[{ts}] ")
        label = escape(f"  {label}... ")
        frame = escape(frame)
        elapsed = escape(f"{elapsed} elapsed")
        return (
            f'<span style="color:{LOG_DIM};">{prefix}</span>'
            f'<span style="color:{TEXT};">{label}</span>'
            f'<span style="color:{LOG_CYAN};">{frame}</span> '
            f'<span style="color:{LOG_DIM};">{elapsed}</span>'
        )

    def _log_color(self, text: str) -> str:
        stripped = text.strip()
        if not stripped:
            return TEXT
        if stripped == "Scriber" or set(stripped) == {"─"} or stripped.startswith("["):
            return LOG_CYAN
        if "model:" in stripped:
            return LOG_CYAN
        if (
            stripped.startswith("✓")
            or stripped.startswith("Saved to:")
            or stripped.startswith("Output folder:")
            or stripped.startswith("Completed ")
        ):
            return LOG_GREEN
        if (
            stripped.startswith("⚠")
            or "no speaker label" in stripped
            or stripped.startswith("Stopped by user")
            or stripped.startswith("Please select")
        ):
            return LOG_YELLOW
        if stripped.startswith("✗") or stripped.startswith("Error:"):
            return LOG_RED
        if "complete" in stripped or stripped.startswith("Done in"):
            return LOG_GREEN
        if stripped.startswith("Audio length:"):
            return LOG_DIM
        return TEXT
