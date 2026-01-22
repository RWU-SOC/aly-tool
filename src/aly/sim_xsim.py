# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Vivado XSIM simulator backend."""

import os
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional

from aly.backends import (
    SimulatorBackend,
    SimulationResult,
    ToolLanguageSupport,
    UnsupportedLanguageError,
)
from aly import log


class XsimBackend(SimulatorBackend):
    """Xilinx Vivado XSIM simulator backend.

    Supports: SystemVerilog, Verilog, VHDL
    """

    SUPPORTED_LANGUAGES = {"systemverilog", "verilog", "vhdl"}

    def __init__(
        self, tool_config, project_root: Path, language: str = "systemverilog"
    ):
        # Accept both dict and SimToolConfig
        if isinstance(tool_config, dict):
            config_dict = tool_config
        elif hasattr(tool_config, "bin"):
            # SimToolConfig or similar object
            config_dict = {
                "bin": tool_config.bin,
                "vlog": getattr(tool_config, "vlog", None),
                "vhdl": getattr(tool_config, "vhdl", None),
                "xelab": getattr(tool_config, "xelab", None),
                "compile_opts": getattr(tool_config, "compile_opts", []),
                "elab_opts": getattr(tool_config, "elab_opts", []),
                "run_opts": getattr(tool_config, "run_opts", []),
            }
        else:
            config_dict = {}

        super().__init__(config_dict, project_root)
        self.language = language.lower()
        self.vlog_bin = config_dict.get("vlog", "xvlog")
        self.vhdl_bin = config_dict.get("vhdl", "xvhdl")
        self.xelab_bin = config_dict.get("xelab", "xelab")
        self.xsim_bin = config_dict.get("bin", "xsim")

        # Validate language support
        if not ToolLanguageSupport.simulator_supports("xsim", self.language):
            raise UnsupportedLanguageError(
                "xsim", self.language, self.SUPPORTED_LANGUAGES
            )

    def compile(
        self,
        sources: List[Path],
        top: str,
        output_dir: Path,
        includes: Optional[List[Path]] = None,
        defines: Optional[Dict[str, str]] = None,
        filelist: Optional[Path] = None,
        **kwargs,
    ) -> bool:
        """Compile with xvlog/xvhdl based on language.

        Args:
            sources: List of source files to compile
            top: Top module name
            output_dir: Output directory for compilation
            includes: List of include directories
            defines: Dict of defines (key=name, value=optional value or None)
            filelist: Optional filelist (.f file) to use instead of sources
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Select compiler based on language
        if self.language == "vhdl":
            return self._compile_vhdl(sources, output_dir, includes, filelist)
        else:
            return self._compile_verilog(
                sources, output_dir, includes, defines, filelist
            )

    def _compile_verilog(
        self,
        sources: List[Path],
        output_dir: Path,
        includes: Optional[List[Path]] = None,
        defines: Optional[Dict[str, str]] = None,
        filelist: Optional[Path] = None,
    ) -> bool:
        """Compile Verilog/SystemVerilog with xvlog."""
        # Build xvlog command
        cmd = [self.vlog_bin]

        # Add language flag
        if self.language == "systemverilog":
            cmd.append("--sv")  # SystemVerilog
        # For plain verilog, no --sv flag needed

        cmd.append("--incr")  # Incremental compilation
        cmd.append("--relax")  # Relaxed checking rules

        # Add include directories
        if includes:
            for inc in includes:
                cmd.extend(["-i", str(inc)])

        # Add defines - use separate -d for each, no =value syntax for boolean defines
        if defines:
            for key, val in defines.items():
                # Only add =value if value is not None/empty and not boolean-like
                if val and val not in ("1", "true", "True", ""):
                    cmd.extend(["-d", f"{key}={val}"])
                else:
                    cmd.extend(["-d", key])

        # Use filelist if provided, otherwise add sources directly
        if filelist and filelist.exists():
            cmd.extend(["-f", str(filelist)])
            log.inf(f"Compiling from filelist: {filelist}")
        else:
            for src in sources:
                cmd.append(str(src))
            log.inf(f"Compiling {len(sources)} files with xvlog ({self.language})")
        log.dbg(f"Command: {' '.join(cmd)}")

        import shutil

        # Find the actual executable path
        vlog_path = shutil.which(self.vlog_bin)
        if vlog_path:
            cmd[0] = vlog_path

        result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True)

        # Save log
        log_file = output_dir / "xvlog.log"
        log_file.write_text(result.stdout + "\n" + result.stderr)

        if result.returncode != 0:
            log.err(f"Compilation failed (exit {result.returncode})")
            log.err(f"See {log_file}")
            # Print last 20 lines of error
            lines = result.stderr.split("\n")
            for line in lines[-20:]:
                if line.strip():
                    log.err(f"  {line}")
            return False

        log.success("Compilation successful")
        return True

    def _compile_vhdl(
        self,
        sources: List[Path],
        output_dir: Path,
        includes: Optional[List[Path]] = None,
        filelist: Optional[Path] = None,
    ) -> bool:
        """Compile VHDL with xvhdl."""
        # Build xvhdl command
        cmd = [self.vhdl_bin]
        cmd.append("--incr")  # Incremental compilation
        cmd.append("--relax")  # Relaxed checking rules

        # VHDL 2008 support
        cmd.append("--2008")

        # Use filelist if provided, otherwise add sources directly
        if filelist and filelist.exists():
            cmd.extend(["-f", str(filelist)])
            log.inf(f"Compiling from filelist: {filelist}")
        else:
            for src in sources:
                cmd.append(str(src))
            log.inf(f"Compiling {len(sources)} VHDL files with xvhdl")
        log.dbg(f"Command: {' '.join(cmd)}")

        import shutil

        # Find the actual executable path
        vhdl_path = shutil.which(self.vhdl_bin)
        if vhdl_path:
            cmd[0] = vhdl_path

        result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True)

        # Save log
        log_file = output_dir / "xvhdl.log"
        log_file.write_text(result.stdout + "\n" + result.stderr)

        if result.returncode != 0:
            log.err(f"VHDL Compilation failed (exit {result.returncode})")
            log.err(f"See {log_file}")
            lines = result.stderr.split("\n")
            for line in lines[-20:]:
                if line.strip():
                    log.err(f"  {line}")
            return False

        log.success("VHDL Compilation successful")
        return True

    def elaborate(
        self, top: str, output_dir: Path, snapshot: Optional[str] = None, **kwargs
    ) -> bool:
        """Elaborate with xelab.

        Args:
            top: Top module name
            output_dir: Output directory
            snapshot: Optional snapshot name (defaults to {top}_snapshot)
        """
        snapshot_name = snapshot or f"{top}_snapshot"

        cmd = [self.xelab_bin]
        cmd.extend(["-debug", "typical"])  # Enable typical debug visibility
        cmd.extend(["-relax"])  # Relaxed checking
        cmd.extend(["-top", top])  # Top module
        cmd.extend(["-snapshot", snapshot_name])  # Snapshot name

        log.inf(f"Elaborating {top} (snapshot: {snapshot_name})")
        log.dbg(f"Command: {' '.join(cmd)}")

        import shutil

        xelab_path = shutil.which(self.xelab_bin)
        if xelab_path:
            cmd[0] = xelab_path

        result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True)

        # Save log
        log_file = output_dir / "xelab.log"
        log_file.write_text(result.stdout + "\n" + result.stderr)

        if result.returncode != 0:
            log.err(f"Elaboration failed (exit {result.returncode})")
            log.err(f"See {log_file}")
            # Print last 20 lines
            lines = result.stderr.split("\n")
            for line in lines[-20:]:
                if line.strip():
                    log.err(f"  {line}")
            return False

        log.success("Elaboration successful")
        return True

    def simulate(
        self,
        top: str,
        output_dir: Path,
        waves: bool = False,
        gui: bool = False,
        plusargs: Optional[List[str]] = None,
        timeout: Optional[int] = None,
        snapshot: Optional[str] = None,
        **kwargs,
    ) -> SimulationResult:
        """Run simulation with xsim.

        Args:
            top: Top module name
            output_dir: Output directory
            waves: Enable waveform capture
            gui: Launch GUI mode
            plusargs: Plusargs to pass to simulation
            timeout: Timeout in seconds
            snapshot: Optional snapshot name (defaults to {top}_snapshot)
        """
        start_time = time.time()
        snapshot_name = snapshot or f"{top}_snapshot"

        cmd = [self.xsim_bin]
        cmd.append(snapshot_name)  # Snapshot name

        # Waveform dump
        waveform_file = None
        vcd_file = None

        if gui:
            cmd.append("--gui")        
        elif waves:
            # Generate both WDB (Xilinx format) and VCD (for GTKWave)
            waveform_file = output_dir / f"{snapshot_name}.wdb"
            vcd_file = output_dir / f"{snapshot_name}.vcd"

            # Create TCL script to generate VCD
            # Note: When using --tclbatch, do NOT use --runall (TCL handles the run)
            tcl_file = output_dir / f"{snapshot_name}_vcd.tcl"
            tcl_file.write_text(f"""open_vcd {vcd_file}
log_vcd *
run all
close_vcd
quit
""")

            cmd.extend(["--wdb", str(waveform_file)])
            cmd.extend(["--tclbatch", str(tcl_file)])
        else:
            # No waves, just run all
            cmd.extend(["--runall"])

        # Add plusargs
        if plusargs:
            for arg in plusargs:
                # Quote the plusarg value to handle paths with special characters
                cmd.extend(["--testplusarg", f'"{arg}"'])

        # Log file
        log_file = output_dir / "xsim.log"
        cmd.extend(["--log", str(log_file)])

        log.inf(f"Running simulation: {snapshot_name}")
        log.inf(f"Command: {' '.join(cmd)}")

        import shutil

        xsim_path = shutil.which(self.xsim_bin)
        if xsim_path:
            cmd[0] = xsim_path

        try:
            # GUI mode: launch non-blocking process
            if gui:
                log.inf("Launching xsim GUI...")

                # On Windows, use shell=True for proper path handling
                use_shell = os.name == "nt"
                if use_shell:
                    cmd_str = " ".join(cmd)
                    proc = subprocess.Popen(
                        cmd_str,
                        cwd=output_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                    )
                else:
                    proc = subprocess.Popen(
                        cmd,
                        cwd=output_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )

                # Check if process starts successfully (wait briefly)
                try:
                    proc.wait(timeout=2)
                    # Process exited quickly - likely an error
                    stdout, stderr = proc.communicate()
                    duration = time.time() - start_time
                    log.err("xsim GUI failed to start")
                    if stderr:
                        log.err(stderr.decode())

                    return SimulationResult(
                        success=False,
                        duration=duration,
                        log_file=log_file,
                        return_code=proc.returncode,
                        stdout=stdout.decode() if stdout else "",
                        stderr=stderr.decode() if stderr else "",
                    )
                except subprocess.TimeoutExpired:
                    # Still running after 2s - GUI launched successfully
                    duration = time.time() - start_time
                    log.success("xsim GUI launched")

                    return SimulationResult(
                        success=True,
                        duration=duration,
                        log_file=log_file,
                        waveform_file=waveform_file
                        if waveform_file and waveform_file.exists()
                        else None,
                        return_code=0,
                        stdout="",
                        stderr="",
                    )

            # Batch mode: run and wait for completion
            else:
                # On Windows, use shell=True to properly handle quoting of plusarg values
                # that contain paths with colons and slashes
                use_shell = os.name == "nt"
                if use_shell:
                    # Convert list to string for shell execution
                    cmd_str = " ".join(cmd)
                    result = subprocess.run(
                        cmd_str,
                        cwd=output_dir,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        shell=True,
                    )
                else:
                    result = subprocess.run(
                        cmd,
                        cwd=output_dir,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                    )

                duration = time.time() - start_time

                # Check for success indicators in output
                success = result.returncode == 0
                output_text = result.stdout + result.stderr

                # Look for test pass/fail indicators
                if "TEST PASSED" in output_text or "PASS" in output_text:
                    success = True
                elif "TEST FAILED" in output_text or "ERROR" in output_text:
                    success = False

                if success:
                    log.success(f"Simulation passed ({duration:.2f}s)")
                else:
                    log.err(f"Simulation failed (exit {result.returncode})")

                # Prefer VCD over WDB for GTKWave compatibility
                final_waveform = None
                if vcd_file and vcd_file.exists():
                    final_waveform = vcd_file
                elif waveform_file and waveform_file.exists():
                    final_waveform = waveform_file

                return SimulationResult(
                    success=success,
                    duration=duration,
                    log_file=log_file,
                    waveform_file=final_waveform,
                    return_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            log.err(f"Simulation timeout after {duration:.2f}s")

            return SimulationResult(
                success=False,
                duration=duration,
                log_file=log_file,
                return_code=-1,
                stdout="",
                stderr="Timeout",
            )
