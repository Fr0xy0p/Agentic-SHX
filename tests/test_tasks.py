"""Unit tests for background TaskManager and ManageTaskTool."""

import time
from pathlib import Path
from agentic_shx.tasks.manager import TaskManager
from agentic_shx.tasks.tool import ManageTaskTool

def test_task_manager_sync_and_async(tmp_path):
    tm = TaskManager(tasks_dir=tmp_path)

    # 1. Fast command finishes synchronously
    finished, output, task = tm.launch(command="echo 'quick output'", cwd=str(tmp_path), wait_ms=2000)
    assert finished is True
    assert "quick output" in output

    # 2. Long command gets backgrounded
    finished_bg, notice, task_bg = tm.launch(command="sleep 10", cwd=str(tmp_path), wait_ms=300)
    assert finished_bg is False
    assert "continuing in background" in notice
    assert task_bg.is_alive is True

    # 3. Test list and status via tool
    tool = ManageTaskTool(task_manager=tm)
    list_res = tool.execute(action="list")
    assert list_res.success is True
    assert task_bg.task_id in list_res.output

    status_res = tool.execute(action="status", task_id=task_bg.task_id)
    assert status_res.success is True
    assert "RUNNING" in status_res.output

    # 4. Kill task
    kill_res = tool.execute(action="kill", task_id=task_bg.task_id)
    assert kill_res.success is True
    assert "Successfully killed" in kill_res.output

