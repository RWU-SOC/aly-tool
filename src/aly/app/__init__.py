# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Built-in ALY commands."""

import argparse
import shutil
import sys
from pathlib import Path

from aly import log
from aly.commands import AlyCommand, CommandError
from aly.configuration import Configuration
from aly.util import find_tool, find_aly_root
from aly import __version__


class Info(AlyCommand):
    """Display ALY configuration and toolchain status."""
    
    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            'info',
            help='display configuration and toolchain status'
        )
        return parser
    
    def run(self, args, unknown_args):
        log.banner("ALY Configuration")
        
        # Project info
        project_root = find_aly_root()
        if project_root:
            log.inf(f"Project Root: {project_root}")
            build_dir = project_root / '.aly_build'
            log.inf(f"Build Directory: {build_dir}")
        else:
            log.wrn("Not in an ALY project (no .aly directory found)")
        
        # Toolchain status
        print(f"\n{log.Colors.BOLD}Toolchains:{log.Colors.RESET}")
        
        # RISC-V toolchain
        riscv_tools = {
            'gcc': 'riscv64-unknown-elf-gcc',
            'as': 'riscv64-unknown-elf-as',
            'ld': 'riscv64-unknown-elf-ld',
            'objcopy': 'riscv64-unknown-elf-objcopy',
        }
        
        riscv_ok = all(find_tool(t) for t in riscv_tools.values())
        status = f"{log.Colors.GREEN}✓ Ready{log.Colors.RESET}" if riscv_ok else f"{log.Colors.RED}✗ Not Found{log.Colors.RESET}"
        print(f"  RISC-V: {status}")
        
        # Vivado toolchain
        vivado_tools = {
            'xvlog': 'xvlog.bat',
            'xelab': 'xelab.bat',
            'xsim': 'xsim.bat',
        }
        
        vivado_ok = all(find_tool(t) for t in vivado_tools.values())
        status = f"{log.Colors.GREEN}✓ Ready{log.Colors.RESET}" if vivado_ok else f"{log.Colors.RED}✗ Not Found{log.Colors.RESET}"
        print(f"  Vivado: {status}")
        
        print()
        return 0


class Clean(AlyCommand):
    """Remove build artifacts."""
    
    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            'clean',
            help='remove build artifacts'
        )
        return parser
    
    def run(self, args, unknown_args):
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")
        
        build_dir = project_root / '.aly_build'
        
        if build_dir.exists():
            log.inf(f"Removing {build_dir}")
            shutil.rmtree(build_dir)
            log.success("Build directory cleaned")
        else:
            log.inf("Build directory doesn't exist, nothing to clean")
        
        return 0


class Version(AlyCommand):
    """Show ALY version."""
    
    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            'version',
            help='show ALY version'
        )
        return parser
    
    def run(self, args, unknown_args):
        print(f"ALY version {__version__}")
        print(f"Python {sys.version}")
        return 0


# Import firmware and init commands from app/
from aly.app.firmware import Firmware
from aly.app.init import Init
from aly.app.simulate import Simulate
from aly.app.synthesize import Synthesize
from aly.app.gen_mem import GenMem
from aly.app.regress import Regress

# Built-in commands list
BUILTIN_COMMANDS = [
    Info,
    Init,
    Firmware,
    Simulate,
    Synthesize,
    GenMem,
    Regress,
    Clean,
    Version,
]
