# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Lint command - runs static analysis on RTL sources.

This module provides RTL linting capabilities using various backends:
- Verilator (default, open-source)
- Spyglass (commercial)
- HAL (commercial)
- Slang (open-source)

Architecture:
    The Lint command discovers RTL sources from the project configuration
    and runs the selected linter tool. Results are parsed and displayed
    in a unified format regardless of the backend used.

Usage:
    aly lint                      # Lint all RTL files
    aly lint --module uart        # Lint specific module
    aly lint --tool verilator     # Use specific linter
    aly lint --warnings           # Show warnings too
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from aly import log
from aly.commands import AlyCommand
from aly.util import find_aly_root, find_tool, run_command
from aly.config import ProjectConfig


@dataclass
class LintResult:
    """Result of a lint run."""

    success: bool
    error_count: int
    warning_count: int
    info_count: int
    messages: List[Dict[str, Any]]
    duration: float


class LinterBackend:
    """Base class for linter backends."""

    name: str = "base"

    def __init__(self, config: Dict[str, Any], project_root: Path):
        self.config = config
        self.project_root = project_root

    def check_available(self) -> bool:
        """Check if the linter is available."""
        raise NotImplementedError

    def lint(
        self,
        sources: List[Path],
        top: Optional[str],
        includes: List[Path],
        defines: Dict[str, str],
        output_dir: Path,
        warnings: bool = True,
    ) -> LintResult:
        """Run linting on sources."""
        raise NotImplementedError


class VerilatorLinter(LinterBackend):
    """Verilator-based linter backend.

    Uses Verilator's --lint-only mode which performs static analysis
    without generating simulation code. This catches:
    - Synthesis/simulation mismatches
    - Undriven signals
    - Unused variables
    - Width mismatches
    - Implicit declarations
    """

    name = "verilator"

    def check_available(self) -> bool:
        """Check if Verilator is available."""
        return find_tool("verilator") is not None

    def lint(
        self,
        sources: List[Path],
        top: Optional[str],
        includes: List[Path],
        defines: Dict[str, str],
        output_dir: Path,
        warnings: bool = True,
    ) -> LintResult:
        """Run Verilator lint-only mode."""
        import time

        start_time = time.time()
        messages = []
        error_count = 0
        warning_count = 0
        info_count = 0

        # Build command
        cmd = ["verilator", "--lint-only"]

        # Wall for all warnings
        if warnings:
            cmd.append("-Wall")
        else:
            cmd.append("-Wno-fatal")

        # Add top module
        if top:
            cmd.extend(["--top-module", top])

        # Add includes
        for inc in includes:
            cmd.append(f"+incdir+{inc}")

        # Add defines
        for key, value in defines.items():
            if value:
                cmd.append(f"+define+{key}={value}")
            else:
                cmd.append(f"+define+{key}")

        # Add sources
        for src in sources:
            cmd.append(str(src))

        log.dbg(f"Running: {' '.join(cmd)}")

        # Run verilator
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            # Parse output
            output = result.stderr + result.stdout
            for line in output.splitlines():
                if "%Error" in line or "Error-" in line:
                    error_count += 1
                    messages.append(
                        {"level": "error", "message": line, "tool": "verilator"}
                    )
                    log.err(line)
                elif "%Warning" in line or "Warning-" in line:
                    warning_count += 1
                    messages.append(
                        {"level": "warning", "message": line, "tool": "verilator"}
                    )
                    if warnings:
                        log.wrn(line)
                elif "%Info" in line:
                    info_count += 1
                    messages.append(
                        {"level": "info", "message": line, "tool": "verilator"}
                    )

            success = result.returncode == 0 and error_count == 0

        except FileNotFoundError:
            log.err("Verilator not found in PATH")
            success = False

        duration = time.time() - start_time

        return LintResult(
            success=success,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            messages=messages,
            duration=duration,
        )


class SlangLinter(LinterBackend):
    """Slang-based linter backend.

    Slang is an open-source SystemVerilog compiler with excellent
    standards compliance. Good for checking SystemVerilog syntax.
    """

    name = "slang"

    def check_available(self) -> bool:
        """Check if slang is available."""
        return find_tool("slang") is not None

    def lint(
        self,
        sources: List[Path],
        top: Optional[str],
        includes: List[Path],
        defines: Dict[str, str],
        output_dir: Path,
        warnings: bool = True,
    ) -> LintResult:
        """Run slang linting."""
        import time

        start_time = time.time()
        messages = []
        error_count = 0
        warning_count = 0
        info_count = 0

        # Build command
        cmd = ["slang", "--lint-only"]

        if top:
            cmd.extend(["--top", top])

        for inc in includes:
            cmd.extend(["-I", str(inc)])

        for key, value in defines.items():
            if value:
                cmd.extend(["-D", f"{key}={value}"])
            else:
                cmd.extend(["-D", key])

        for src in sources:
            cmd.append(str(src))

        log.dbg(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            output = result.stderr + result.stdout
            for line in output.splitlines():
                if "error:" in line.lower():
                    error_count += 1
                    messages.append(
                        {"level": "error", "message": line, "tool": "slang"}
                    )
                    log.err(line)
                elif "warning:" in line.lower():
                    warning_count += 1
                    messages.append(
                        {"level": "warning", "message": line, "tool": "slang"}
                    )
                    if warnings:
                        log.wrn(line)
                elif "note:" in line.lower():
                    info_count += 1
                    messages.append({"level": "info", "message": line, "tool": "slang"})

            success = result.returncode == 0 and error_count == 0

        except FileNotFoundError:
            log.err("slang not found in PATH")
            success = False

        duration = time.time() - start_time

        return LintResult(
            success=success,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            messages=messages,
            duration=duration,
        )


# Available linter backends
LINTER_BACKENDS = {
    "verilator": VerilatorLinter,
    "slang": SlangLinter,
}


class Lint(AlyCommand):
    """Run static analysis on RTL sources.

    This command provides unified access to various RTL linting tools.
    By default, it uses Verilator's lint-only mode which catches common
    RTL coding issues without generating simulation models.

    The command reads RTL configuration from .aly/rtl.yaml to find
    source files, include directories, and defines.

    Examples:
        aly lint                        # Lint all RTL
        aly lint --module uart          # Lint specific module
        aly lint --tool slang           # Use slang linter
        aly lint --no-warnings          # Errors only
    """

    @staticmethod
    def add_parser(parser_adder):
        """Add lint command parser."""
        parser = parser_adder.add_parser(
            "lint",
            help="run static analysis on RTL",
            description="Run static analysis/linting on RTL sources using "
            "Verilator, slang, or other supported linters.",
        )
        parser.add_argument(
            "--tool",
            choices=list(LINTER_BACKENDS.keys()),
            default="verilator",
            help="linter tool to use (default: verilator)",
        )
        parser.add_argument(
            "--module",
            "-m",
            help="lint specific module only (sets --top for the linter)",
        )
        parser.add_argument(
            "--top",
            help="top module name for linting context",
        )
        parser.add_argument(
            "--no-warnings",
            action="store_true",
            help="suppress warnings, show only errors",
        )
        parser.add_argument(
            "files",
            nargs="*",
            help="specific files to lint (default: all RTL from config)",
        )
        return parser

    def run(self, args, unknown_args):
        """Execute lint command."""
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        # Load configuration
        try:
            config = ProjectConfig.load(project_root)
        except Exception as e:
            self.die(f"Failed to load configuration: {e}")

        # Get linter backend
        backend_class = LINTER_BACKENDS.get(args.tool)
        if not backend_class:
            self.die(f"Unsupported linter: {args.tool}")

        # Get tool config (optional)
        tool_config = config.lint.get_tool(args.tool)

        backend = backend_class(tool_config, project_root)

        # Check tool availability
        if not backend.check_available():
            self.die(
                f"{args.tool} not found in PATH.\n"
                f"Install it or use a different linter with --tool"
            )

        # Check if the module name is valid
        if not args.files and not args.module:
            self.die("Module name must be specified with --module when no files are given")

        # Setup output directory
        output_dir = project_root / "build" / "lint" / args.tool / (args.module or "all")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Collect RTL sources
        sources = []
        includes = []
        defines = {}

        # Get sources
        if args.files:
            sources = [Path(f).resolve() for f in args.files]
        else:
            rtl_module = config.get_rtl_module(args.module)
            
            if not rtl_module:
                self.die("The RTL module not found in configuration")

            # 1. Resolve package dependencies first (must come before RTL modules)
            pkg_files = config.resolve_package_dep_files(rtl_module.obj)
            sources.extend(pkg_files)

            # 2. Resolve RTL/IP dependencies (returns UnitRef objects)
            rtl_dep_refs = config.resolve_rtl_deps(rtl_module.obj)
            for ref in rtl_dep_refs:
                module = ref.obj  # RTLModule
                manifest = ref.manifest  # RTLManifest

                # Get files for this specific module (packages + module files)
                sources.extend(manifest.get_files_for_module(module.name))
                includes.extend(manifest.get_include_dirs())
                defines.update(manifest.get_defines())

            # 3. Add RTL module files
            sources.extend(rtl_module.obj.resolve_files())

            # 4. Add includes/defines from module's parent manifest
            includes.extend(rtl_module.manifest.get_include_dirs())
            defines.update(rtl_module.manifest.get_defines())

        if not sources:
            self.die("No RTL sources found")


        # Get top module (fallback to module name if not specified)
        top = args.top or rtl_module.obj.top or rtl_module.obj.name

        # Run lint
        log.banner(f"RTL Linting ({args.tool})")
        log.inf(f"Sources: {len(sources)} files")
        log.inf(f"Top: {top}")

        result = backend.lint(
            sources=sources,
            top=top,
            includes=includes,
            defines=defines,
            output_dir=output_dir,
            warnings=not args.no_warnings,
        )

        # Print summary
        print()
        log.inf("=== Summary ===")
        log.inf(f"Duration: {result.duration:.2f}s")
        log.inf(f"Errors: {result.error_count}")
        log.inf(f"Warnings: {result.warning_count}")

        if result.success:
            log.success("Lint PASSED")
            return 0
        else:
            log.err("Lint FAILED")
            return 1
