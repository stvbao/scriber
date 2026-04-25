from __future__ import annotations

import json
import sys

from PyQt6.QtCore import QObject, QProcess, pyqtSignal

from scriber.core.batch import BatchConfig, run_batch


class Worker(QObject):
    log = pyqtSignal(str)           # append new line
    log_replace = pyqtSignal(str)   # overwrite last line
    reset_timer = pyqtSignal()      # reset elapsed timer for new file
    suspend_pulse = pyqtSignal()    # pause the pulse while busy (no log_replace)
    resume_pulse = pyqtSignal(str)  # resume elapsed pulse for long-running work
    done = pyqtSignal()

    def __init__(self, config: dict):
        super().__init__()
        self.config = BatchConfig.from_mapping(config)
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        self._stdout_buffer = ""
        self._stderr_buffer = ""
        self._done_emitted = False
        self._stopping = False
        self._config_json = json.dumps(self.config.to_mapping(), ensure_ascii=False)

        self._process.started.connect(self._write_config)
        self._process.readyReadStandardOutput.connect(self._read_stdout)
        self._process.readyReadStandardError.connect(self._read_stderr)
        self._process.errorOccurred.connect(self._on_error)
        self._process.finished.connect(self._on_finished)

    def start(self):
        program, args = _worker_command()
        self._process.start(program, args)

    def stop(self):
        self.terminate()

    def terminate(self):
        self._stopping = True
        if self.isRunning():
            self._process.kill()
        else:
            self._emit_done()

    def wait(self, timeout_ms: int | None = 0) -> bool:
        timeout = -1 if timeout_ms is None else timeout_ms
        return self._process.waitForFinished(timeout)

    def isRunning(self) -> bool:
        return self._process.state() != QProcess.ProcessState.NotRunning

    def _write_config(self):
        self._process.write(self._config_json.encode("utf-8"))
        self._process.closeWriteChannel()

    def _read_stdout(self):
        chunk = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
        self._stdout_buffer += chunk
        while "\n" in self._stdout_buffer:
            line, self._stdout_buffer = self._stdout_buffer.split("\n", 1)
            self._handle_stdout_line(line)

    def _read_stderr(self):
        chunk = bytes(self._process.readAllStandardError()).decode("utf-8", errors="replace")
        self._stderr_buffer += chunk

    def _handle_stdout_line(self, line: str):
        if not line:
            return
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            self.log.emit(line)
            return

        event_type = event.get("type")
        message = event.get("message") or ""
        if event_type == "log":
            self.log.emit(message)
        elif event_type == "log_replace":
            self.log_replace.emit(message)
        elif event_type == "reset_timer":
            self.reset_timer.emit()
        elif event_type == "suspend_pulse":
            self.suspend_pulse.emit()
        elif event_type == "resume_pulse":
            self.resume_pulse.emit(message)

    def _on_error(self, error):
        if self._stopping:
            return
        error_name = getattr(error, "name", str(error))
        self.log.emit(f"✗ Worker process error: {error_name}")
        self._emit_done()

    def _on_finished(self, exit_code: int, _exit_status):
        self._read_stdout()
        self._read_stderr()
        if self._stdout_buffer.strip():
            self._handle_stdout_line(self._stdout_buffer.strip())
        self._stdout_buffer = ""

        if exit_code != 0 and not self._stopping:
            self.log.emit(f"✗ Worker process failed with exit code {exit_code}.")
            details = self._stderr_buffer.strip()
            if details:
                for line in details.splitlines()[-8:]:
                    self.log.emit(f"  Error: {line}")

        self._emit_done()

    def _emit_done(self):
        if self._done_emitted:
            return
        self._done_emitted = True
        self.done.emit()


def run_worker_from_stdin() -> int:
    try:
        config = BatchConfig.from_mapping(json.loads(sys.stdin.read()))
    except Exception as e:
        _emit_process_event("log", "✗ Worker process could not read its configuration.")
        _emit_process_event("log", f"  Error: {e}")
        return 2

    try:
        run_batch(config, _emit_process_event)
    except Exception as e:
        _emit_process_event("log", "✗ Worker process failed.")
        _emit_process_event("log", f"  Error: {e}")
        return 1
    return 0


def _emit_process_event(event_type: str, message: str = "", **payload):
    event = {"type": event_type, "message": message, **payload}
    print(json.dumps(event, ensure_ascii=False), flush=True)


def _worker_command() -> tuple[str, list[str]]:
    if getattr(sys, "frozen", False):
        return sys.executable, ["__gui_worker__"]
    return sys.executable, ["-m", "scriber", "__gui_worker__"]


if __name__ == "__main__":
    raise SystemExit(run_worker_from_stdin())
