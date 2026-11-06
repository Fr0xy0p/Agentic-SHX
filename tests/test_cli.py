"""Unit tests for CLI flags and shell integration."""

import subprocess
import sys

def test_cli_version():
    res = subprocess.run([sys.executable, "-m", "agentic_shx.cli", "-v"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Agentic-SHX v" in res.stdout or "Agentic-SHX v" in res.stderr

def test_cli_init_zsh():
    res = subprocess.run([sys.executable, "-m", "agentic_shx.cli", "init", "zsh"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Agentic-SHX Shell Integration for zsh" in res.stdout
    assert "alias agn=" in res.stdout

def test_cli_init_bash():
    res = subprocess.run([sys.executable, "-m", "agentic_shx.cli", "init", "bash"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Agentic-SHX Shell Integration for bash" in res.stdout
    assert "alias agn=" in res.stdout


def test_cli_positional_help():
    res = subprocess.run([sys.executable, "-m", "agentic_shx.cli", "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "prompt_args" in res.stdout


