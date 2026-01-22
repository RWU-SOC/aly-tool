# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Utility functions for ALY."""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional


def run_command(
    cmd: List[str], cwd: Optional[Path] = None, check=True
) -> subprocess.CompletedProcess:
    """Run a command and return the result.

    Args:
        cmd: Command as list of strings
        cwd: Working directory
        check: Raise exception on non-zero exit

    Returns:
        CompletedProcess instance
    """
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def find_tool(name: str) -> Optional[str]:
    """Find a tool in PATH.

    Args:
        name: Tool name to find

    Returns:
        Full path to tool or None
    """
    return shutil.which(name)


def find_aly_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """Find ALY project root by looking for .aly directory.

    Args:
        start_path: Where to start searching (uses cwd if None)

    Returns:
        Path to project root or None
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Walk up directory tree
    while current != current.parent:
        if (current / ".aly").is_dir():
            return current
        current = current.parent

    return None
