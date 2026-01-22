# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Built-in ALY commands."""

from aly.app.basic import Clean, Info, Refresh, Version
from aly.app.config import Config
from aly.app.constraints import Constraints
from aly.app.firmware import Firmware
from aly.app.rtl import RTL
from aly.app.init import Init
from aly.app.ip import IP
from aly.app.lint import Lint
from aly.app.program import Program
from aly.app.simulate import Simulate
from aly.app.synthesize import Synthesize
from aly.app.terminal import Terminal

# Built-in commands list
BUILTIN_COMMANDS = [
    # Core commands
    Info,
    Init,
    Config,
    # Development workflow
    RTL,
    Firmware,
    Lint,
    Simulate,
    Synthesize,
    # IP & Constraints
    Constraints,
    IP,
    # Deployment
    Program,
    Terminal,
    # Utilities
    Clean,
    Refresh,
    Version,
]
