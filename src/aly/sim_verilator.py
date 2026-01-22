# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Verilator simulator backend."""

import subprocess
import time
from pathlib import Path
from typing import List, Optional, Dict

from aly import log
from aly.backends import (
    SimulatorBackend,
    SimulationResult,
    ToolLanguageSupport,
    UnsupportedLanguageError,
)


class VerilatorBackend(SimulatorBackend):
    """Verilator simulator backend (compile to C++ executable).

    Supports: SystemVerilog, Verilog (NO VHDL support)
    """

    SUPPORTED_LANGUAGES = {"systemverilog", "verilog"}

    def __init__(
        self, tool_config, project_root: Path, language: str = "systemverilog"
    ):
        """
        Initialize Verilator backend.

        Args:
            tool_config: Tool configuration (dict or SimToolConfig)
            project_root: Project root path
            language: HDL language (systemverilog or verilog)
        """
        # Accept both dict and SimToolConfig
        if isinstance(tool_config, dict):
            config_dict = tool_config
        elif hasattr(tool_config, "bin"):
            # SimToolConfig or similar object
            config_dict = {
                "bin": tool_config.bin,
                "trace": getattr(tool_config, "trace", True),
                "coverage": getattr(tool_config, "coverage", False),
                "compile_opts": getattr(tool_config, "compile_opts", []),
                "run_opts": getattr(tool_config, "run_opts", []),
            }
        else:
            config_dict = {}

        super().__init__(config_dict, project_root)
        self.tool_config = config_dict
        self.logger = log
        self.language = language.lower()

        # Validate language support
        if not ToolLanguageSupport.simulator_supports("verilator", self.language):
            raise UnsupportedLanguageError(
                "verilator", self.language, self.SUPPORTED_LANGUAGES
            )

    def compile(
        self,
        sources: List[Path],
        top: str,
        output_dir: Path,
        includes: Optional[List[Path]] = None,
        defines: Optional[Dict[str, str]] = None,
        work_lib: str = "work",
    ) -> bool:
        """
        Compile RTL sources with Verilator to C++.

        Args:
            sources: List of source files to compile
            top: Top module name
            output_dir: Directory for build outputs
            includes: Include directories
            defines: Preprocessor defines
            work_lib: Work library name (unused for Verilator)

        Returns:
            True if compilation succeeded, False otherwise
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        verilator = self.tool_config.get("bin", "verilator")

        # Check for C++ testbench
        tb_cpp = output_dir.parent.parent / "tb" / f"{top}.cpp"
        has_cpp_tb = tb_cpp.exists()

        # Build verilator command
        cmd = [
            verilator,
            "--cc",  # Generate C++ output
            "-Wno-fatal",  # Don't treat warnings as errors
            "--timing",  # Enable timing support for delays and event controls
            "--top-module",
            top,
            "-Mdir",
            str(output_dir / "obj_dir"),
        ]

        # Only add --exe and --build if we have a C++ testbench
        if has_cpp_tb:
            cmd.extend(["--exe", "--build"])
        else:
            # Create minimal C++ wrapper for SystemVerilog testbenches with timing support
            wrapper_cpp = output_dir / f"{top}_wrapper.cpp"
            wrapper_cpp.write_text(f"""
#include "V{top}.h"
#include "verilated.h"

#if VM_TRACE
#include "verilated_vcd_c.h"
#endif

int main(int argc, char** argv) {{
    Verilated::commandArgs(argc, argv);

    V{top}* dut = new V{top};

#if VM_TRACE
    Verilated::traceEverOn(true);
    VerilatedVcdC* tfp = new VerilatedVcdC;
    dut->trace(tfp, 99);
    tfp->open("{top}.vcd");
#endif

    // Initialize simulation
    dut->eval();
#if VM_TRACE
    tfp->dump(0);
#endif

    // Run simulation - let Verilator's timing scheduler handle time advancement
    while (!Verilated::gotFinish()) {{
        // Evaluate model with timing
        dut->eval();

#if VM_TRACE
        // Dump trace at current time
        tfp->dump(Verilated::time());
#endif

        // Advance time through Verilator's timing scheduler
        if (!dut->eventsPending()) break;
        Verilated::time(dut->nextTimeSlot());
    }}

#if VM_TRACE
    // Final dump and close
    tfp->dump(Verilated::time());
    tfp->close();
    delete tfp;
#endif

    delete dut;
    return 0;
}}
""")
            cmd.extend(["--exe", str(wrapper_cpp), "--build"])
            self.logger.inf(f"Created C++ wrapper: {wrapper_cpp}")

        # Add trace support if requested
        trace = self.tool_config.get("trace", True)
        if trace:
            cmd.extend(
                [
                    "--trace",  # Enable VCD tracing
                    "--trace-structs",  # Trace structs
                ]
            )

        # Add coverage if requested
        coverage = self.tool_config.get("coverage", False)
        if coverage:
            cmd.append("--coverage")

        # Add include directories
        if includes:
            for inc in includes:
                cmd.extend(["-I" + str(inc)])

        # Add defines
        if defines:
            for key, value in defines.items():
                if value:
                    cmd.append(f"-D{key}={value}")
                else:
                    cmd.append(f"-D{key}")

        # Add C++ testbench if exists
        if has_cpp_tb:
            cmd.append(str(tb_cpp))
            self.logger.dbg(f"Using C++ testbench: {tb_cpp}")

        # Add sources
        for src in sources:
            cmd.append(str(src))

        # Compile
        log_file = output_dir / f"{top}_verilator.log"
        self.logger.inf("Compiling with Verilator...")
        self.logger.dbg(f"Command: {' '.join(cmd)}")

        with open(log_file, "w") as f:
            result = subprocess.run(
                cmd, cwd=output_dir, stdout=f, stderr=subprocess.STDOUT, text=True
            )

        if result.returncode != 0:
            self.logger.err(f"Verilator compilation failed. See {log_file}")
            # Print last 30 lines of log
            with open(log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-30:]:
                    self.logger.err(line.rstrip())
            return False

        self.logger.success("Verilator compilation successful")
        return True

    def elaborate(
        self,
        top: str,
        output_dir: Path,
        work_lib: str = "work",
        timescale: str = "1ns/1ps",
    ) -> bool:
        """
        Elaborate design (happens during compile for Verilator).

        Args:
            top: Top module name
            output_dir: Directory with compiled design
            work_lib: Work library name (unused)
            timescale: Default timescale (unused)

        Returns:
            True (elaboration happens during compile)
        """
        # Verilator elaborates during compilation
        exe_path = output_dir / "obj_dir" / f"V{top}"
        if exe_path.exists() or (exe_path.with_suffix(".exe").exists()):
            self.logger.dbg("Verilator executable ready")
            return True
        else:
            self.logger.err("Verilator executable not found after compilation")
            return False

    def simulate(
        self,
        top: str,
        output_dir: Path,
        waves: bool = False,
        gui: bool = False,
        plusargs: Optional[List[str]] = None,
        timeout: Optional[int] = None,
        work_lib: str = "work",
    ) -> SimulationResult:
        """
        Run Verilator-compiled executable.

        Args:
            top: Top module name to simulate
            output_dir: Directory with compiled executable
            waves: Enable waveform dumping (VCD generated in obj_dir)
            gui: Ignored - use --gtkwave flag in simulate command instead
            plusargs: Additional plusargs to pass to simulator
            timeout: Simulation timeout in seconds
            work_lib: Work library name (unused)

        Returns:
            SimulationResult with status and outputs
        """
        _ = gui  # GUI handled by simulate.py via --gtkwave flag
        # Find executable
        exe_path = output_dir / "obj_dir" / f"V{top}"
        if not exe_path.exists():
            exe_path = exe_path.with_suffix(".exe")  # Windows

        if not exe_path.exists():
            self.logger.err(f"Verilator executable not found: {exe_path}")
            return SimulationResult(
                success=False,
                duration=0.0,
                log_file=output_dir / f"{top}_sim.log",
                waveform_file=None,
            )

        # Build command
        cmd = [str(exe_path)]

        # Waveform setup - VCD is generated in obj_dir when waves enabled
        obj_dir = output_dir / "obj_dir"
        waveform_file = None
        if waves:
            waveform_file = obj_dir / f"{top}.vcd"

        # Add plusargs
        if plusargs:
            for arg in plusargs:
                cmd.append(f"+{arg}")

        # Run simulation
        log_file = output_dir / f"{top}_sim.log"
        self.logger.inf(f"Running Verilator simulation...")
        self.logger.dbg(f"Command: {' '.join(cmd)}")

        start_time = time.time()
        success = False

        try:
            with open(log_file, "w") as f:
                result = subprocess.run(
                    cmd,
                    cwd=obj_dir,  # Run from obj_dir so VCD is generated there
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                    text=True,
                )

            duration = time.time() - start_time

            # Read log file to check for success indicators
            # (some testbenches use $stop which returns non-zero but test passed)
            output_text = ""
            if log_file.exists():
                with open(log_file, "r") as f:
                    output_text = f.read()

            # Check for success/failure indicators in output
            # Start with return code, then override based on output content
            success = result.returncode == 0

            # Check for explicit failure indicators first
            has_failure = (
                "Simulation failed" in output_text
                or "TEST FAILED" in output_text
                or "FATAL" in output_text
                or "$error" in output_text
                or "FAIL:" in output_text
            )

            # Check for explicit success indicators
            has_success = (
                "Simulation succeeded" in output_text
                or "TEST PASSED" in output_text
                or "Errors: 0" in output_text
            )

            # $stop without failure indicators is considered success
            # (testbenches commonly use $stop to end simulation)
            has_stop = "$stop" in output_text or "Verilog $stop" in output_text

            if has_failure:
                success = False
            elif has_success:
                success = True
            elif has_stop and not has_failure:
                # $stop without errors is success
                success = True

            if success:
                self.logger.success(f"Simulation completed in {duration:.2f}s")
            else:
                self.logger.err(f"Simulation failed. See {log_file}")
                # Print last 20 lines
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    for line in lines[-20:]:
                        self.logger.err(line.rstrip())

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.logger.wrn(f"Simulation timed out after {timeout}s")

        return SimulationResult(
            success=success,
            duration=duration,
            log_file=log_file,
            waveform_file=waveform_file
            if waveform_file and waveform_file.exists()
            else None,
        )
