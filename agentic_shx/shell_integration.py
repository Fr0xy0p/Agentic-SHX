"""Shell integration for directory navigation, environment persistence, and clipboard support."""

import os
import platform
import subprocess
import shlex
from pathlib import Path
from typing import Optional, Tuple

SHELL_STATE_COMMANDS = {
    "cd",
    "pushd",
    "popd",
    "source",
    ".",
    "export",
    "unset",
    "alias",
    "unalias",
}

def is_shell_state_command(command: str) -> bool:
    """Check if a shell command alters the parent shell's working directory or environment."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        tokens = list(lexer)
    except Exception:
        tokens = command.split()

    delimiters = {";", "&&", "||", "|", "&", "\n"}
    expect_command = True

    for token in tokens:
        if expect_command:
            # Skip environment variable assignments before the command (e.g. FOO=1 cd ...)
            if "=" in token and not token.startswith("="):
                continue
            # Strip path and leading backslash (e.g. /usr/bin/cd or \cd)
            raw_token = token.lstrip("\\")
            cmd_name = Path(raw_token).name or raw_token
            if cmd_name in SHELL_STATE_COMMANDS:
                return True
            expect_command = False
        elif token in delimiters:
            expect_command = True

    return False

def copy_to_clipboard(text: str) -> bool:
    """Copy given text to system clipboard across macOS, Linux, and Windows."""
    system = platform.system()
    try:
        if system == "Darwin":
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, close_fds=True)
            p.communicate(input=text.encode("utf-8"))
            return p.returncode == 0
        elif system == "Linux":
            for cmd in (["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
                try:
                    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, close_fds=True)
                    p.communicate(input=text.encode("utf-8"))
                    if p.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
        elif system == "Windows":
            p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, close_fds=True)
            p.communicate(input=text.encode("utf-8"))
            return p.returncode == 0
    except Exception:
        pass
    return False

def handoff_command_to_shell(command: str) -> bool:
    """Write command to SHX_CMD_FILE so parent shell function wrapper executes it."""
    cmd_file = os.environ.get("SHX_CMD_FILE")
    if cmd_file:
        try:
            Path(cmd_file).write_text(command.strip(), encoding="utf-8")
            return True
        except Exception:
            pass
    return False

def get_shell_init_script(shell_name: str) -> str:
    """Return the shell function wrapper that enables directory navigation and environment changes."""
    s = shell_name.strip().lower()
    if s == "zsh":
        return """# shx shell integration for zsh
shx() {
    local tmp
    tmp="$(mktemp -t shx_cmd.XXXXXX)"
    SHX_CMD_FILE="$tmp" command shx "$@"
    local ret=$?
    if [[ -f "$tmp" ]]; then
        local cmd
        cmd="$(cat "$tmp")"
        rm -f "$tmp"
        if [[ -n "$cmd" ]]; then
            print -s "$cmd" 2>/dev/null || true
            eval "$cmd"
            ret=$?
        fi
    fi
    return $ret
}
"""
    elif s == "bash":
        return """# shx shell integration for bash
shx() {
    local tmp
    tmp="$(mktemp -t shx_cmd.XXXXXX)"
    SHX_CMD_FILE="$tmp" command shx "$@"
    local ret=$?
    if [ -f "$tmp" ]; then
        local cmd
        cmd="$(cat "$tmp")"
        rm -f "$tmp"
        if [ -n "$cmd" ]; then
            history -s "$cmd" 2>/dev/null || true
            eval "$cmd"
            ret=$?
        fi
    fi
    return $ret
}
"""
    elif s == "fish":
        return """# shx shell integration for fish
function shx
    set -l tmp (mktemp -t shx_cmd.XXXXXX)
    env SHX_CMD_FILE="$tmp" command shx $argv
    set -l ret $status
    if test -f "$tmp"
        set -l cmd (cat "$tmp")
        rm -f "$tmp"
        if test -n "$cmd"
            history add "$cmd"
            eval "$cmd"
            set ret $status
        end
    end
    return $ret
end
"""
    else:
        return """# shx shell integration
shx() {
    local tmp
    tmp="$(mktemp -t shx_cmd.XXXXXX)"
    SHX_CMD_FILE="$tmp" command shx "$@"
    local ret=$?
    if [ -f "$tmp" ]; then
        local cmd
        cmd="$(cat "$tmp")"
        rm -f "$tmp"
        if [ -n "$cmd" ]; then
            eval "$cmd"
            ret=$?
        fi
    fi
    return $ret
}
"""

def install_shell_integration(shell_name: Optional[str] = None) -> Tuple[bool, str]:
    """Append shell integration line to user's shell configuration file."""
    if not shell_name:
        shell_env = os.environ.get("SHELL", "")
        shell_name = Path(shell_env).name if shell_env else ("zsh" if platform.system() == "Darwin" else "bash")
    shell_clean = shell_name.strip().lower()

    home = Path.home()
    if shell_clean == "zsh":
        rc_path = home / ".zshrc"
    elif shell_clean == "bash":
        if platform.system() == "Darwin":
            rc_path = home / ".bash_profile" if (home / ".bash_profile").exists() else home / ".bashrc"
        else:
            rc_path = home / ".bashrc"
    elif shell_clean == "fish":
        rc_path = home / ".config" / "fish" / "config.fish"
    else:
        rc_path = home / ".profile"

    init_cmd = f'eval "$(shx init {shell_clean})"'
    if shell_clean == "fish":
        init_cmd = "shx init fish | source"

    try:
        content = ""
        if rc_path.exists():
            content = rc_path.read_text(encoding="utf-8")

        if "shx init" in content:
            return True, f"Shell integration is already installed in {rc_path}"

        rc_path.parent.mkdir(parents=True, exist_ok=True)
        with open(rc_path, "a", encoding="utf-8") as f:
            f.write(f"\n# shx shell integration (enables directory navigation & environment persistence)\n{init_cmd}\n")

        return True, f"Successfully installed shell integration into {rc_path}. Run 'source {rc_path}' to activate."
    except Exception as e:
        return False, f"Could not write to {rc_path}: {e}"
