"""Cryptic flag dictionary and command explainer engine."""

import shlex
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class FlagInfo:
    flag: str
    name: str
    description: str

WRAPPER_COMMANDS = {
    "sudo",
    "doas",
    "nohup",
    "time",
    "nice",
    "ionice",
    "strace",
    "ltrace",
    "valgrind",
    "xargs",
    "catchsegv",
    "parallel",
    "timeout",
}

def unwrap_command(cmd: str, args: List[str]) -> Tuple[str, List[str], List[str]]:
    """Unwraps wrapper commands (e.g. sudo, xargs, nohup, timeout) down to the core target command."""
    wrappers: List[str] = []
    current_cmd = cmd.lstrip("\\").split("/")[-1]
    current_args = list(args)

    while current_cmd in WRAPPER_COMMANDS and current_args:
        wrappers.append(current_cmd)
        idx = 0
        while idx < len(current_args) and current_args[idx].startswith("-"):
            if current_args[idx] in ("-u", "-g", "-n", "-s", "-I", "-P", "-k"):
                idx += 2
            else:
                idx += 1
        if idx < len(current_args):
            current_cmd = current_args[idx].lstrip("\\").split("/")[-1]
            current_args = current_args[idx + 1 :]
        else:
            break

    return current_cmd, current_args, wrappers

# Offline database of notoriously cryptic Unix/POSIX/GNU/BSD flags
CRYPTIC_FLAG_DATABASE: Dict[str, Dict[str, Tuple[str, str]]] = {
    "tar": {
        "-x": ("Extract", "Extract files from an archive"),
        "-c": ("Create", "Create a new archive"),
        "-v": ("Verbose", "Verbosely list files processed"),
        "-z": ("Gzip", "Filter archive through gzip (.tar.gz / .tgz)"),
        "-j": ("Bzip2", "Filter archive through bzip2 (.tar.bz2)"),
        "-J": ("XZ", "Filter archive through xz (.tar.xz)"),
        "-f": ("File", "Use given archive file instead of tape drive"),
        "-p": ("Preserve Permissions", "Preserve file permissions/modes"),
        "-C": ("Change Directory", "Change to target directory before performing operations"),
        "--strip-components": ("Strip Leading Components", "Remove leading directory components from file names"),
        "-t": ("List", "List archive contents without extracting"),
    },
    "find": {
        "-type": ("File Type", "Filter by type (f = regular file, d = directory, l = symlink)"),
        "-name": ("Name Pattern", "Case-sensitive filename pattern matching"),
        "-iname": ("Case-Insensitive Name", "Case-insensitive filename pattern matching"),
        "-mtime": ("Modified Time", "Files modified n*24 hours ago (+n = older than, -n = newer than)"),
        "-mmin": ("Modified Minutes", "Files modified n minutes ago"),
        "-size": ("File Size", "Filter by size (+100M = larger than 100MB, -1k = less than 1KB)"),
        "-exec": ("Execute Command", "Execute command on each match (terminated with ';' or '+')"),
        "-delete": ("Delete Matches", "Permanently delete matching files directly"),
        "-maxdepth": ("Max Recursion Depth", "Descend at most n directory levels below starting point"),
        "-perm": ("Permissions", "Find files matching specific permission mode bits"),
        "-empty": ("Empty File/Directory", "Find files or directories that are zero bytes / empty"),
    },
    "rsync": {
        "-a": ("Archive Mode", "Equivalent to -rlptgoD (recursive, copy symlinks, preserve perms, times, owner, group)"),
        "-v": ("Verbose", "Increase verbosity"),
        "-z": ("Compress", "Compress file data during transfer"),
        "-P": ("Progress & Partial", "Equivalent to --partial --progress (keep partially transferred files and show progress)"),
        "--delete": ("Delete Extraneous", "Delete files in destination that do not exist in source"),
        "-e": ("Remote Shell", "Specify remote shell to use (e.g., ssh)"),
        "-h": ("Human-Readable", "Output numbers in human-readable format"),
        "-n": ("Dry Run", "Perform a trial run with no changes made"),
    },
    "curl": {
        "-s": ("Silent Mode", "Silent or quiet mode, don't show progress meter or error messages"),
        "-S": ("Show Error", "When used with -s, show error message if it fails"),
        "-L": ("Follow Redirects", "Follow HTTP 3xx redirects automatically"),
        "-O": ("Remote Name", "Write output to a local file named like the remote file"),
        "-o": ("Output File", "Write output to specific destination file"),
        "-I": ("Head Only", "Fetch HTTP headers only"),
        "-X": ("Request Method", "Specify custom request method (GET, POST, PUT, DELETE)"),
        "-H": ("Header", "Pass custom HTTP header to server"),
        "-d": ("Data", "Sends specified data in HTTP POST request"),
        "-k": ("Insecure", "Allow insecure server connections when using SSL"),
        "-f": ("Fail Fast", "Fail silently on server errors (HTTP 400+)"),
    },
    "grep": {
        "-r": ("Recursive", "Recursively read all files under each directory"),
        "-R": ("Recursive Dereference", "Recursively read all files under each directory, following all symlinks"),
        "-i": ("Ignore Case", "Case-insensitive matching"),
        "-v": ("Invert Match", "Select non-matching lines"),
        "-n": ("Line Number", "Prefix each line of output with the 1-based line number"),
        "-l": ("Files with Matches", "Suppress normal output; instead print name of each input file with matches"),
        "-E": ("Extended Regex", "Interpret pattern as an extended regular expression (ERE)"),
        "-P": ("Perl Regex", "Interpret pattern as a Perl-compatible regular expression (PCRE)"),
        "-o": ("Only Matching", "Print only matched (non-empty) parts of matching line"),
        "-c": ("Count", "Suppress normal output; instead print count of matching lines"),
    },
    "git": {
        "-p": ("Patch Mode", "Interactively choose hunks of patch in the working tree"),
        "-b": ("Branch", "Create a new branch with git checkout / switch"),
        "-m": ("Message", "Commit or move message"),
        "-a": ("All", "Stage all tracked modified and deleted files"),
        "--hard": ("Hard Reset", "Reset index and working tree; any changes to tracked files are discarded"),
        "--cached": ("Cached / Staged", "Show changes between index and HEAD commit"),
        "--amend": ("Amend Commit", "Replace tip of current branch by creating a new commit"),
    },
    "chmod": {
        "-R": ("Recursive", "Change files and directories recursively"),
        "-v": ("Verbose", "Output a diagnostic for every file processed"),
        "-c": ("Changes Only", "Like verbose but report only when a change is made"),
    },
    "chown": {
        "-R": ("Recursive", "Operate on files and directories recursively"),
        "-v": ("Verbose", "Output a diagnostic for every file processed"),
    },
    "ps": {
        "-a": ("All Processes", "Select all processes except both session leaders and processes not associated with a terminal"),
        "-u": ("User Oriented", "Display user-oriented format"),
        "-x": ("Lift Terminal Restriction", "Include processes without a controlling terminal"),
        "-aux": ("Full Process List", "List all running processes across all users with terminal info"),
        "-ef": ("Standard Full Format", "List all processes in full standard format"),
    },
    "netstat": {
        "-t": ("TCP Sockets", "Display TCP connections"),
        "-u": ("UDP Sockets", "Display UDP connections"),
        "-l": ("Listening Sockets", "Show only listening sockets"),
        "-p": ("Process Info", "Show PID and name of program to which each socket belongs"),
        "-n": ("Numeric Addresses", "Show numerical addresses instead of resolving hosts"),
    },
}

TAR_FLAGS = {"x", "c", "v", "z", "j", "J", "f", "p", "t", "C"}

def explain_local_command(command: str) -> List[FlagInfo]:
    """Inspect shell command and extract known cryptic flags using offline database."""
    results: List[FlagInfo] = []
    clean_cmd = command.strip()

    try:
        lexer = shlex.shlex(clean_cmd, posix=True, punctuation_chars=True)
        segments: List[List[str]] = []
        current: List[str] = []
        while True:
            tok = lexer.get_token()
            if not tok:
                if current:
                    segments.append(current)
                break
            if tok in (";", "&&", "||", "|", "&", "\n"):
                if current:
                    segments.append(current)
                    current = []
            else:
                current.append(tok)
    except Exception:
        segments = [clean_cmd.split()]

    for segment in segments:
        if not segment:
            continue

        raw_cmd = segment[0]
        args = segment[1:]
        current_cmd, remaining_args, _ = unwrap_command(raw_cmd, args)
        cmd_db = CRYPTIC_FLAG_DATABASE.get(current_cmd, {})
        if not cmd_db:
            continue

        first_arg = True
        for token in remaining_args:
            # Handle dash-less tar flags: e.g. tar xzvf archive.tar.gz
            if current_cmd == "tar" and first_arg and not token.startswith("-"):
                first_arg = False
                if all(ch in TAR_FLAGS for ch in token):
                    for char in token:
                        single_flag = f"-{char}"
                        if single_flag in cmd_db:
                            name, desc = cmd_db[single_flag]
                            results.append(FlagInfo(flag=f"{current_cmd} {single_flag}", name=name, description=desc))
                    continue

            first_arg = False

            if token in cmd_db:
                name, desc = cmd_db[token]
                results.append(FlagInfo(flag=f"{current_cmd} {token}", name=name, description=desc))
            elif token.startswith("-") and len(token) > 2 and not token.startswith("--"):
                if current_cmd == "ps" and token == "-aux":
                    name, desc = cmd_db["-aux"]
                    results.append(FlagInfo(flag="ps -aux", name=name, description=desc))
                else:
                    for char in token[1:]:
                        single_flag = f"-{char}"
                        if single_flag in cmd_db:
                            name, desc = cmd_db[single_flag]
                            results.append(FlagInfo(flag=f"{current_cmd} {single_flag}", name=name, description=desc))

    return results

