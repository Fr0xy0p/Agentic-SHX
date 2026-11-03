"""Unit tests for built-in tools."""

import tempfile
import os
from pathlib import Path
from agentic_shx.tools.file_ops import ReadFileTool, WriteFileTool, EditFileTool
from agentic_shx.tools.bash import BashTool
from agentic_shx.tools.search import SearchFilesTool, ListFilesTool
from agentic_shx.tools.registry import ToolRegistry

def test_write_and_read_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        w_tool = WriteFileTool(cwd=tmpdir)
        r_tool = ReadFileTool(cwd=tmpdir)

        # Write
        res_write = w_tool.execute(path="subdir/test.txt", content="line1\nline2\nline3\n")
        assert res_write.success is True

        # Read full
        res_read = r_tool.execute(path="subdir/test.txt")
        assert res_read.success is True
        assert "1 | line1" in res_read.output
        assert "2 | line2" in res_read.output
        assert "3 | line3" in res_read.output

        # Read line range
        res_slice = r_tool.execute(path="subdir/test.txt", start_line=2, end_line=2)
        assert res_slice.success is True
        assert "2 | line2" in res_slice.output
        assert "1 | line1" not in res_slice.output

def test_edit_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        w_tool = WriteFileTool(cwd=tmpdir)
        e_tool = EditFileTool(cwd=tmpdir)
        r_tool = ReadFileTool(cwd=tmpdir)

        w_tool.execute(path="code.py", content="def hello():\n    return 'world'\n")

        # Successful edit
        res_edit = e_tool.execute(
            path="code.py",
            target="return 'world'",
            replacement="return 'universe'"
        )
        assert res_edit.success is True

        res_read = r_tool.execute(path="code.py")
        assert "return 'universe'" in res_read.output

        # Target not found
        res_fail = e_tool.execute(
            path="code.py",
            target="non_existent_text",
            replacement="something"
        )
        assert res_fail.success is False
        assert "not found" in res_fail.error

def test_bash_tool():
    with tempfile.TemporaryDirectory() as tmpdir:
        b_tool = BashTool(cwd=tmpdir)

        # Normal command
        res = b_tool.execute(command="echo 'Agentic-SHX rocks'")
        assert res.success is True
        assert "Agentic-SHX rocks" in res.output

        # Failing command
        res_fail = b_tool.execute(command="exit 42")
        assert res_fail.success is False
        assert "42" in res_fail.error

def test_search_and_list_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        w_tool = WriteFileTool(cwd=tmpdir)
        w_tool.execute(path="a.txt", content="target_keyword here")
        w_tool.execute(path="b.txt", content="nothing to see")

        s_tool = SearchFilesTool(cwd=tmpdir)
        res_search = s_tool.execute(query="target_keyword")
        assert res_search.success is True
        assert "a.txt:1: target_keyword here" in res_search.output

        l_tool = ListFilesTool(cwd=tmpdir)
        res_list = l_tool.execute(pattern="*.txt")
        assert res_list.success is True
        assert "a.txt" in res_list.output
        assert "b.txt" in res_list.output

def test_tool_registry():
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = ToolRegistry.create_default(cwd=tmpdir)
        declarations = registry.get_declarations()
        assert len(declarations) >= 7
        tool_names = [d["function"]["name"] for d in declarations]
        assert "bash" in tool_names
        assert "read_file" in tool_names
        assert "write_file" in tool_names
        assert "edit_file" in tool_names

