# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Logging utilities for ALY."""

import sys
from typing import NoReturn


# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


# Global verbosity level
_verbosity = 1  # 0=quiet, 1=normal, 2=verbose, 3=debug


def set_verbosity(level: int):
    """Set global verbosity level."""
    global _verbosity
    _verbosity = level


def dbg(*args, **kwargs):
    """Log debug message (verbosity >= 3)."""
    if _verbosity >= 3:
        print(f"{Colors.CYAN}[DEBUG]{Colors.RESET}", *args, **kwargs)


def inf(*args, **kwargs):
    """Log info message (verbosity >= 1)."""
    if _verbosity >= 1:
        print(f"{Colors.BLUE}[INFO]{Colors.RESET}", *args, **kwargs)


def wrn(*args, **kwargs):
    """Log warning message (verbosity >= 1)."""
    if _verbosity >= 1:
        print(
            f"{Colors.YELLOW}[WARNING]{Colors.RESET}", *args, **kwargs, file=sys.stderr
        )


def err(*args, **kwargs):
    """Log error message (always shown)."""
    print(f"{Colors.RED}[ERROR]{Colors.RESET}", *args, **kwargs, file=sys.stderr)


def die(*args, **kwargs) -> NoReturn:
    """Log error and exit."""
    err(*args, **kwargs)
    sys.exit(1)


def banner(msg: str):
    """Print a banner message."""
    if _verbosity >= 1:
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{msg:^60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*60}{Colors.RESET}\n")


def success(msg: str):
    """Print success message."""
    if _verbosity >= 1:
        print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")
