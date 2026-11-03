"""Background task and process supervisor."""

import os
import time
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

DEFAULT_TASKS_DIR = Path.home() / ".agentic_shx" / "tasks"

def _utc_now_str() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class BackgroundTask:
    task_id: str
    command: str
    pid: int
    process: subprocess.Popen
    log_file: Path
    start_time: str
    is_daemon: bool = False
    returncode: Optional[int] = None

    @property
    def is_alive(self) -> bool:
        if self.process.poll() is None:
            return True
        self.returncode = self.process.returncode
        return False

    @property
    def status_str(self) -> str:
        if self.is_alive:
            return "RUNNING"
        return f"DONE (code {self.returncode})" if self.returncode == 0 else f"ERROR (code {self.returncode})"


class TaskManager:
    """Oversees background processes, logging, and status tracking."""

    def __init__(self, tasks_dir: Optional[Path] = None):
        self.tasks_dir = tasks_dir or DEFAULT_TASKS_DIR
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.tasks: Dict[str, BackgroundTask] = {}
        self._counter = 0

    def launch(
        self,
        command: str,
        cwd: str,
        is_daemon: bool = False,
        wait_ms: int = 5000
    ) -> tuple[bool, str, Optional[BackgroundTask]]:
        """
        Executes a command. If it completes within wait_ms and is not a daemon,
        returns (True, output, None). Otherwise backgrounds it and returns (False, notice, task).
        """
        self._counter += 1
        task_id = f"task-{self._counter}"
        log_file = self.tasks_dir / f"{task_id}.log"

        log_handle = open(log_file, "w+", encoding="utf-8")

        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                executable="/bin/bash" if os.path.exists("/bin/bash") else None
            )

            task = BackgroundTask(
                task_id=task_id,
                command=command,
                pid=proc.pid,
                process=proc,
                log_file=log_file,
                start_time=_utc_now_str(),
                is_daemon=is_daemon
            )
            self.tasks[task_id] = task

            # If user explicitly requested daemon, background immediately
            if is_daemon:
                return False, f"Process launched in background as daemon. TaskId: {task_id} (PID: {proc.pid})", task

            # Wait up to wait_ms before backgrounding
            wait_seconds = wait_ms / 1000.0
            start_poll = time.time()
            while time.time() - start_poll < wait_seconds:
                if proc.poll() is not None:
                    # Finished within wait time!
                    task.returncode = proc.returncode
                    log_handle.flush()
                    output = log_file.read_text(encoding="utf-8")
                    return True, output, task
                time.sleep(0.1)

            # Still running -> Background it!
            return False, f"Command exceeded {wait_ms}ms, continuing in background as TaskId: '{task_id}' (PID: {proc.pid}). Output logs at: {log_file}", task

        except Exception as e:
            return True, f"Failed to execute command: {str(e)}", None

    def list_tasks(self) -> str:
        """Formatted list of all tracked background tasks."""
        if not self.tasks:
            return "No background tasks currently active or tracked."
        lines = ["ID       | PID   | STATUS     | COMMAND", "---------+-------+------------+-----------------------------------"]
        for tid, t in self.tasks.items():
            cmd_preview = t.command if len(t.command) < 40 else t.command[:37] + "..."
            lines.append(f"{t.task_id:8} | {t.pid:5} | {t.status_str:10} | {cmd_preview}")
        return "\n".join(lines)

    def get_status(self, task_id: str, tail_lines: int = 25) -> str:
        """Inspect status and recent logs of a task."""
        task = self.tasks.get(task_id)
        if not task:
            return f"Task '{task_id}' not found."

        logs = ""
        if task.log_file.exists():
            try:
                all_lines = task.log_file.read_text(encoding="utf-8").splitlines()
                recent = all_lines[-tail_lines:] if len(all_lines) > tail_lines else all_lines
                logs = "\n".join(recent)
            except Exception as e:
                logs = f"(Error reading log file: {e})"

        return (
            f"TaskId: {task.task_id}\n"
            f"PID: {task.pid}\n"
            f"Status: {task.status_str}\n"
            f"Started: {task.start_time}\n"
            f"Recent output logs (last {tail_lines} lines):\n"
            f"---\n{logs or '(no output yet)'}"
        )

    def send_input(self, task_id: str, input_str: str) -> str:
        """Deliver stdin input to a running task."""
        task = self.tasks.get(task_id)
        if not task:
            return f"Task '{task_id}' not found."
        if not task.is_alive:
            return f"Task '{task_id}' is no longer running (Status: {task.status_str})."
        try:
            if task.process.stdin:
                task.process.stdin.write(input_str + "\n")
                task.process.stdin.flush()
                return f"Successfully sent input to task {task_id}."
            return f"Task {task_id} stdin is not available."
        except Exception as e:
            return f"Failed to deliver input: {e}"

    def kill(self, task_id: str) -> str:
        """Terminate a background task."""
        task = self.tasks.get(task_id)
        if not task:
            return f"Task '{task_id}' not found."
        if not task.is_alive:
            return f"Task '{task_id}' is already terminated."
        try:
            task.process.terminate()
            time.sleep(0.2)
            if task.process.poll() is None:
                task.process.kill()
            return f"Successfully killed task '{task_id}' (PID {task.pid})."
        except Exception as e:
            return f"Failed to kill task '{task_id}': {e}"
