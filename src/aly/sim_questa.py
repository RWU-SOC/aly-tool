# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Questa/ModelSim simulator backend."""

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


class QuestaBackend(SimulatorBackend):
    """Questa/ModelSim simulator backend implementation.

    Supports: SystemVerilog, Verilog, VHDL
    """

    SUPPORTED_LANGUAGES = {"systemverilog", "verilog", "vhdl"}

    def __init__(
        self, tool_config, project_root: Path, language: str = "systemverilog"
    ):
        """
        Initialize Questa backend.

        Args:
            tool_config: Tool configuration (dict or SimToolConfig)
            project_root: Project root path
            language: HDL language
        """
        # Accept both dict and SimToolConfig
        if isinstance(tool_config, dict):
            config_dict = tool_config
        elif hasattr(tool_config, "bin"):
            # SimToolConfig or similar object
            config_dict = {
                "bin": tool_config.bin,
                "vlog": getattr(tool_config, "vlog", "vlog"),
                "vcom": getattr(tool_config, "vcom", "vcom"),
                "vlib": getattr(tool_config, "vlib", "vlib"),
                "vsim": getattr(tool_config, "vsim", "vsim"),
                "compile_opts": getattr(tool_config, "compile_opts", []),
                "elab_opts": getattr(tool_config, "elab_opts", []),
                "run_opts": getattr(tool_config, "run_opts", []),
            }
        else:
            config_dict = {}

        super().__init__(config_dict, project_root)
        self.tool_config = config_dict
        self.logger = log
        self.language = language.lower()

        # Validate language support
        if not ToolLanguageSupport.simulator_supports("questa", self.language):
            raise UnsupportedLanguageError(
                "questa", self.language, self.SUPPORTED_LANGUAGES
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
        Compile RTL sources using vlog/vcom.

        Args:
            sources: List of source files to compile
            top: Top module name
            output_dir: Directory for build outputs
            includes: Include directories
            defines: Preprocessor defines
            work_lib: Work library name

        Returns:
            True if compilation succeeded, False otherwise
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create work library if it doesn't exist
        work_dir = output_dir / work_lib
        if not work_dir.exists():
            vlib = self.tool_config.get("vlib", "vlib")
            self.logger.dbg(f"Creating work library: {work_lib}")
            result = subprocess.run(
                [vlib, work_lib], cwd=output_dir, capture_output=True, text=True
            )
            if result.returncode != 0:
                self.logger.err(f"Failed to create work library: {result.stderr}")
                return False

        # Build vlog command
        vlog = self.tool_config.get("vlog", "vlog")
        cmd = [vlog, "-sv", "-work", work_lib]

        # Add include directories
        if includes:
            for inc in includes:
                cmd.extend(["+incdir+" + str(inc)])

        # Add defines
        if defines:
            for key, value in defines.items():
                if value:
                    cmd.append(f"+define+{key}={value}")
                else:
                    cmd.append(f"+define+{key}")

        # Add lint warnings
        cmd.extend(
            [
                "-lint",
                "-pedanticerrors",
                "-hazards",
            ]
        )

        # Add sources
        for src in sources:
            cmd.append(str(src))

        # Compile
        log_file = output_dir / f"{top}_vlog.log"
        self.logger.inf(f"Compiling with vlog...")
        self.logger.dbg(f"Command: {' '.join(cmd)}")

        with open(log_file, "w") as f:
            result = subprocess.run(
                cmd, cwd=output_dir, stdout=f, stderr=subprocess.STDOUT, text=True
            )

        if result.returncode != 0:
            self.logger.err(f"Compilation failed. See {log_file}")
            # Print last 20 lines of log
            with open(log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    self.logger.err(line.rstrip())
            return False

        self.logger.success("Compilation successful")
        return True

    def elaborate(
        self,
        top: str,
        output_dir: Path,
        work_lib: str = "work",
        timescale: str = "1ns/1ps",
    ) -> bool:
        """
        Elaborate design (no separate step in Questa, happens during vsim).

        Args:
            top: Top module name
            output_dir: Directory with compiled design
            work_lib: Work library name
            timescale: Default timescale

        Returns:
            True (elaboration happens during simulate)
        """
        # Questa doesn't have a separate elaboration step
        # Design is elaborated when vsim is invoked
        self.logger.dbg("Questa elaborates during simulation startup")
        return True

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
        Run simulation using vsim.

        Args:
            top: Top module name to simulate
            output_dir: Directory with elaborated design
            waves: Enable waveform dumping
            gui: Run in GUI mode
            plusargs: Additional plusargs to pass to simulator
            timeout: Simulation timeout in seconds
            work_lib: Work library name

        Returns:
            SimulationResult with status and outputs
        """
        vsim = self.tool_config.get("vsim", "vsim")

        # Build vsim command
        waveform_file = None

        if gui:
            # GUI mode - add do file to load signals
            do_cmds = "log -r /*; "
            cmd = [vsim, "-gui", "-do", do_cmds, f"{work_lib}.{top}"]
        else:
            # Batch mode
            if waves:
                # Enable waveform logging: log all signals, run, then quit
                waveform_file = output_dir / f"{top}.wlf"
                do_cmds = "log -r /*; run -all; quit"
                cmd = [vsim, "-batch", "-do", do_cmds, f"{work_lib}.{top}"]
                cmd.extend(["-wlf", str(waveform_file)])
                # Enable optimization access for waveforms
                cmd.extend(["-voptargs=+acc"])
            else:
                cmd = [vsim, "-batch", "-do", "run -all; quit", f"{work_lib}.{top}"]

        # Add plusargs
        if plusargs:
            for arg in plusargs:
                cmd.append(f"+{arg}")

        # Run simulation
        log_file = output_dir / f"{top}_sim.log"
        self.logger.inf("Running simulation...")
        self.logger.dbg(f"Command: {' '.join(cmd)}")

        start_time = time.time()
        success = False
        duration = 0.0

        if gui:
            # GUI mode: launch process and check if it starts successfully
            self.logger.inf("Launching ModelSim GUI...")
            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=output_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                # Wait briefly to see if process crashes immediately
                try:
                    proc.wait(timeout=2)
                    # Process exited quickly - likely an error
                    stderr = proc.stderr.read().decode() if proc.stderr else ""
                    stdout = proc.stdout.read().decode() if proc.stdout else ""
                    self.logger.err(
                        f"ModelSim GUI exited immediately (code {proc.returncode})"
                    )
                    if stderr:
                        self.logger.err(f"stderr: {stderr}")
                    if stdout:
                        self.logger.err(f"stdout: {stdout}")
                    duration = time.time() - start_time
                except subprocess.TimeoutExpired:
                    # Process is still running after 2s - GUI launched successfully
                    self.logger.success("ModelSim GUI launched")
                    success = True
                    duration = time.time() - start_time
                success = True
                duration = time.time() - start_time
            except Exception as e:
                self.logger.err(f"Failed to launch GUI: {e}")
                duration = time.time() - start_time
        else:
            # Batch mode: run and wait for completion
            try:
                with open(log_file, "w") as f:
                    result = subprocess.run(
                        cmd,
                        cwd=output_dir,
                        stdout=f,
                        stderr=subprocess.STDOUT,
                        timeout=timeout,
                        text=True,
                    )

                duration = time.time() - start_time
                success = result.returncode == 0

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

        # Convert WLF to VCD for GTKWave compatibility
        vcd_file = None
        if waveform_file and waveform_file.exists():
            vcd_file = waveform_file.with_suffix(".vcd")
            wlf2vcd = self.tool_config.get("wlf2vcd", "wlf2vcd")
            try:
                self.logger.dbg(f"Converting WLF to VCD: {vcd_file}")
                conv_result = subprocess.run(
                    [wlf2vcd, str(waveform_file), "-o", str(vcd_file)],
                    cwd=output_dir,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if conv_result.returncode == 0 and vcd_file.exists():
                    self.logger.inf(f"Converted to VCD: {vcd_file}")
                else:
                    self.logger.dbg(f"WLF to VCD conversion failed or not available")
                    vcd_file = None
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self.logger.dbg("wlf2vcd not available, keeping WLF format")
                vcd_file = None

        # Return VCD if available, otherwise WLF
        final_waveform = vcd_file if vcd_file and vcd_file.exists() else (
            waveform_file if waveform_file and waveform_file.exists() else None
        )

        return SimulationResult(
            success=success,
            duration=duration,
            log_file=log_file,
            waveform_file=final_waveform,
        )
