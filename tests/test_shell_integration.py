"""Unit tests for shell integration, navigation, and explainer."""

from pathlib import Path
from agentic_shx.shell_integration import (
    is_shell_state_command,
    get_shell_init_script,
    install_shell_integration,
    handoff_command_to_shell
)
from agentic_shx.explainer import explain_local_command
from agentic_shx.tools.bash import BashTool

def test_is_shell_state_command():
    assert is_shell_state_command("cd ~/CodeForces") is True
    assert is_shell_state_command("cd ..") is True
    assert is_shell_state_command("cd") is True
    assert is_shell_state_command("mkdir foo && cd foo") is True
    assert is_shell_state_command("FOO=1 cd /tmp") is True
    assert is_shell_state_command("pushd /tmp") is True
    assert is_shell_state_command("popd") is True
    assert is_shell_state_command("source .venv/bin/activate") is True
    assert is_shell_state_command(". ~/.bashrc") is True
    assert is_shell_state_command("export MY_VAR=1") is True
    assert is_shell_state_command("unset MY_VAR") is True
    assert is_shell_state_command("alias ll='ls -la'") is True
    assert is_shell_state_command("unalias ll") is True

    assert is_shell_state_command("ls -la") is False
    assert is_shell_state_command("git status") is False
    assert is_shell_state_command("echo 'cd is cool'") is False
    assert is_shell_state_command("cat README.md | grep cd") is False

def test_get_shell_init_script():
    zsh_script = get_shell_init_script("zsh")
    assert "shx()" in zsh_script
    assert "SHX_CMD_FILE" in zsh_script
    assert 'eval "$cmd"' in zsh_script

    bash_script = get_shell_init_script("bash")
    assert "shx()" in bash_script
    assert "history -s" in bash_script

    fish_script = get_shell_init_script("fish")
    assert "function shx" in fish_script
    assert 'eval "$cmd"' in fish_script

def test_install_shell_integration(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    success, msg = install_shell_integration("zsh")
    assert success is True
    zshrc = tmp_path / ".zshrc"
    assert zshrc.exists()
    content = zshrc.read_text(encoding="utf-8")
    assert 'eval "$(shx init zsh)"' in content

    # Second install should detect already installed
    success2, msg2 = install_shell_integration("zsh")
    assert success2 is True
    assert "already installed" in msg2

def test_bash_tool_cd_directory_tracking(tmp_path):
    sub = tmp_path / "subdir"
    sub.mkdir()
    tool = BashTool(cwd=str(tmp_path))
    assert tool.cwd == str(tmp_path)

    # cd into sub
    res = tool.execute(command=f"cd {sub.name}")
    assert res.success is True
    assert Path(tool.cwd).resolve() == sub.resolve()

def test_explain_local_command():
    flags = explain_local_command("tar -xzvf archive.tar.gz")
    assert len(flags) >= 4
    flag_names = {f.name for f in flags}
    assert "Extract" in flag_names
    assert "Gzip" in flag_names
    assert "Verbose" in flag_names
    assert "File" in flag_names
