"""Unit tests for CLI subcommands, flags, and shell integration."""

import subprocess
import sys

def test_cli_version():
    res = subprocess.run([sys.executable, "-m", "agentic_shx.cli", "-v"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Agentic-SHX v" in res.stdout or "Agentic-SHX v" in res.stderr

def test_cli_init_zsh():
    res = subprocess.run([sys.executable, "-m", "agentic_shx.cli", "init", "zsh"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "shx shell integration for zsh" in res.stdout
    assert "SHX_CMD_FILE" in res.stdout

def test_cli_init_bash():
    res = subprocess.run([sys.executable, "-m", "agentic_shx.cli", "init", "bash"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "shx shell integration for bash" in res.stdout
    assert "SHX_CMD_FILE" in res.stdout

def test_cli_info():
    res = subprocess.run([sys.executable, "-m", "agentic_shx.cli", "info"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Environment & System Context" in res.stdout
    assert "gemini/gemini-3.8-flash" in res.stdout

def test_cli_explain():
    res = subprocess.run([sys.executable, "-m", "agentic_shx.cli", "explain", "tar", "-xzvf", "test.tar.gz"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Cryptic Flags Identified" in res.stdout
    assert "Extract" in res.stdout

def test_cli_positional_help():
    res = subprocess.run([sys.executable, "-m", "agentic_shx.cli", "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "prompt_args" in res.stdout
