# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Yosys open-source synthesis backend."""

import subprocess
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

from aly import log
from aly.backends import SynthesisBackend, SynthesisResult


class YosysBackend(SynthesisBackend):
    """Yosys open-source synthesis backend.

    Supports: SystemVerilog, Verilog (NO native VHDL support - requires GHDL plugin)

    Cell Library Flow:
        When a liberty file (.lib) is provided via tool_config["liberty"],
        the backend uses the standard Yosys ASIC flow:
        1. read_verilog - read RTL sources
        2. hierarchy - elaborate design hierarchy
        3. proc; opt; fsm; opt; memory; opt - high-level synthesis
        4. techmap; opt - mapping to internal cell library
        5. dfflibmap -liberty <lib> - mapping flip-flops to cell library
        6. abc -liberty <lib> - mapping logic to cell library
        7. clean - cleanup
        8. write_verilog - write synthesized design
    """

    SUPPORTED_LANGUAGES = {"systemverilog", "verilog"}

    def __init__(self, tool_config: Dict[str, Any], project_root: Path, logger=None):
        """
        Initialize Yosys backend.

        Args:
            tool_config: Tool configuration dict from synth.tools.yosys
                - bin: yosys executable path (default: "yosys")
                - tech: technology target (generic, sky130, ice40, ecp5, asic)
                - liberty: path to liberty file (.lib) for ASIC flow
                - abc_script: custom ABC script file
                - jobs: number of parallel jobs for ABC
            project_root: Project root directory
            logger: Optional logger instance
        """
        super().__init__(tool_config, project_root)
        self.logger = logger or log
        self.tool_config = tool_config or {}

    def synthesize(
        self,
        sources: List[Path],
        top: str,
        output_dir: Path,
        part: Optional[str] = None,
        constraints: Optional[List[Path]] = None,
        includes: Optional[List[Path]] = None,
        defines: Optional[Dict[str, str]] = None,
        jobs: Optional[int] = None,
        **kwargs,
    ) -> SynthesisResult:
        """
        Run Yosys synthesis.

        Args:
            sources: List of RTL source files
            top: Top module name
            output_dir: Directory for outputs
            part: Technology library (e.g., 'sky130', 'asap7', 'generic')
            constraints: SDC constraint files (limited support)
            includes: Include directories
            defines: Preprocessor defines
            jobs: Number of parallel jobs for ABC (if supported)

        Returns:
            SynthesisResult with status and reports
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        reports_dir = output_dir / "reports"
        reports_dir.mkdir(exist_ok=True)

        # Get technology and liberty file
        tech = part or self.tool_config.get("tech", "generic")
        liberty = self.tool_config.get("liberty")

        # Resolve liberty path if relative
        if liberty and not Path(liberty).is_absolute():
            liberty_path = self.project_root / liberty
            if liberty_path.exists():
                liberty = str(liberty_path)

        # Generate Yosys script
        script = self._generate_yosys_script(
            sources=sources,
            top=top,
            tech=tech,
            includes=includes,
            defines=defines,
            liberty=liberty,
            jobs=jobs,
        )

        script_file = output_dir / "synth.ys"
        with open(script_file, "w") as f:
            f.write(script)

        # Run Yosys
        yosys = self.tool_config.get("bin", "yosys")
        cmd = [yosys, "-s", str(script_file)]

        # Add parallel jobs flag if supported
        if jobs and jobs > 1:
            cmd.extend(["-j", str(jobs)])

        log_file = output_dir / "yosys.log"
        self.logger.inf("Running Yosys synthesis...")
        self.logger.dbg(f"Command: {' '.join(cmd)}")

        start_time = time.time()

        with open(log_file, "w") as f:
            result = subprocess.run(
                cmd, cwd=output_dir, stdout=f, stderr=subprocess.STDOUT, text=True
            )

        duration = time.time() - start_time
        success = result.returncode == 0

        if success:
            self.logger.success(f"Synthesis completed in {duration:.2f}s")
            # Parse statistics
            stats = self._parse_stats(log_file)
            if stats:
                self.logger.inf(f"  Cells: {stats.get('num_cells', 'N/A')}")
                self.logger.inf(f"  Wires: {stats.get('num_wires', 'N/A')}")
        else:
            self.logger.err(f"Synthesis failed after {duration:.2f}s")
            # Print last 20 lines of log
            with open(log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    self.logger.err(line.rstrip())

        return SynthesisResult(
            success=success,
            duration=duration,
            reports_dir=reports_dir,
            timing_met=None,  # Yosys doesn't do timing analysis by default
        )

    def get_reports(self, output_dir: Path) -> Dict[str, Path]:
        """
        Get paths to synthesis reports.

        Args:
            output_dir: Synthesis output directory

        Returns:
            Dictionary of report name to file path
        """
        reports_dir = output_dir / "reports"
        if not reports_dir.exists():
            return {}

        reports = {}
        report_files = {
            "stats": "stats.txt",
            "check": "check.txt",
            "hierarchy": "hierarchy.txt",
        }

        for name, filename in report_files.items():
            rpt_path = reports_dir / filename
            if rpt_path.exists():
                reports[name] = rpt_path

        return reports

    def _generate_yosys_script(
        self,
        sources: List[Path],
        top: str,
        tech: str,
        includes: Optional[List[Path]],
        defines: Optional[Dict[str, str]],
        liberty: Optional[str] = None,
        jobs: Optional[int] = None,
    ) -> str:
        """Generate Yosys synthesis script.

        Args:
            sources: RTL source files
            top: Top module name
            tech: Technology target
            includes: Include directories
            defines: Preprocessor defines
            liberty: Path to liberty file for ASIC flow
            jobs: Number of parallel jobs for ABC

        Returns:
            Yosys script content
        """

        script = f"""# Yosys Synthesis Script
# Generated by ALY
# Technology: {tech}
# Top module: {top}

"""

        # Read sources with proper file type detection
        script += "# Read design\n"

        for src in sources:
            ext = src.suffix.lower()
            read_opts = []

            # Add includes and defines for Verilog files
            if ext in [".sv", ".svh", ".v", ".vh"]:
                if ext in [".sv", ".svh"]:
                    read_opts.append("-sv")

                if includes:
                    for inc in includes:
                        read_opts.append(f"-I{inc}")

                if defines:
                    for key, value in defines.items():
                        if value:
                            read_opts.append(f"-D{key}={value}")
                        else:
                            read_opts.append(f"-D{key}")

                opts_str = " ".join(read_opts) if read_opts else ""
                script += f"read_verilog {opts_str} {src}\n"
            elif ext in [".vhd", ".vhdl"]:
                # VHDL requires GHDL plugin
                script += f"# VHDL file (requires GHDL plugin): {src}\n"
                script += f"# ghdl --synth -e {top}  # Alternative: use ghdl plugin\n"
            else:
                # Default to SystemVerilog
                if includes:
                    for inc in includes:
                        read_opts.append(f"-I{inc}")
                if defines:
                    for key, value in defines.items():
                        if value:
                            read_opts.append(f"-D{key}={value}")
                        else:
                            read_opts.append(f"-D{key}")
                opts_str = " ".join(["-sv"] + read_opts) if read_opts else "-sv"
                script += f"read_verilog {opts_str} {src}\n"

        # Elaborate design hierarchy
        script += f"""
# Elaborate design hierarchy
hierarchy -check -top {top}
"""

        # Synthesis flow based on technology and liberty availability
        if liberty:
            # ASIC flow with cell library
            script += self._generate_asic_flow(top, liberty, jobs)
        elif tech == "generic":
            # Generic synthesis (no target technology)
            script += self._generate_generic_flow()
        elif "sky130" in tech.lower():
            # SkyWater 130nm PDK
            script += self._generate_sky130_flow(top)
        elif "ice40" in tech.lower():
            # Lattice iCE40 FPGA
            script += f"""
# iCE40 FPGA synthesis flow
synth_ice40 -top {top}
"""
        elif "ecp5" in tech.lower():
            # Lattice ECP5 FPGA
            script += f"""
# ECP5 FPGA synthesis flow
synth_ecp5 -top {top}
"""
        elif "gowin" in tech.lower():
            # Gowin FPGA
            script += f"""
# Gowin FPGA synthesis flow
synth_gowin -top {top}
"""
        elif "xilinx" in tech.lower():
            # Xilinx FPGA (limited support)
            script += f"""
# Xilinx FPGA synthesis flow
synth_xilinx -top {top}
"""
        else:
            # Default: use synth command
            script += f"""
# Default synthesis flow
synth -top {top}
"""

        # Reports and outputs
        script += """
# Cleanup
clean

# Generate reports
tee -o reports/stats.txt stat
tee -o reports/check.txt check
hierarchy -check > reports/hierarchy.txt

# Write outputs
write_verilog -noattr synth.v
write_json synth.json

# Done
"""

        return script

    def _generate_generic_flow(self) -> str:
        """Generate generic synthesis flow (no target technology)."""
        return """
# Generic synthesis flow (no target technology)
# High-level stuff
proc
opt
fsm
opt
memory
opt

# Mapping to internal cell library
techmap
opt
"""

    def _generate_asic_flow(
        self, top: str, liberty: str, jobs: Optional[int] = None
    ) -> str:
        """Generate ASIC synthesis flow with liberty file.

        Args:
            top: Top module name
            liberty: Path to liberty file
            jobs: Number of parallel threads for ABC

        Returns:
            Yosys script fragment for ASIC flow
        """
        abc_opts = f"-liberty {liberty}"
        if jobs and jobs > 1:
            abc_opts += f" -threads {jobs}"

        return f"""
# ASIC synthesis flow with cell library
# Liberty file: {liberty}

# High-level synthesis
proc
opt
fsm
opt
memory
opt

# Mapping to internal cell library
techmap
opt

# Mapping flip-flops to cell library
dfflibmap -liberty {liberty}

# Mapping logic to cell library
abc {abc_opts}

# Cleanup
clean
"""

    def _generate_sky130_flow(self, top: str) -> str:
        """Generate Sky130 PDK synthesis flow."""
        return f"""
# SkyWater Sky130 PDK synthesis flow
# Note: Requires Sky130 PDK liberty files in path

# High-level synthesis
proc
opt
fsm
opt
memory
opt

# Mapping to internal cell library
techmap
opt

# Map flip-flops to Sky130 cells
# dfflibmap -liberty $SKY130_PDK/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib

# Map logic to Sky130 cells
# abc -liberty $SKY130_PDK/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib

# Alternative: use synth for generic mapping if PDK not available
synth -top {top}

# Cleanup
clean
"""

    def _parse_stats(self, log_file: Path) -> Optional[Dict[str, int]]:
        """
        Parse synthesis statistics from log file.

        Args:
            log_file: Path to Yosys log file

        Returns:
            Dictionary with statistics or None
        """
        try:
            stats = {}
            with open(log_file, "r") as f:
                content = f.read()

                # Look for "Number of cells" line
                for line in content.split("\n"):
                    if "Number of cells:" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            try:
                                stats["num_cells"] = int(parts[1].strip())
                            except ValueError:
                                pass
                    elif "Number of wires:" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            try:
                                stats["num_wires"] = int(parts[1].strip())
                            except ValueError:
                                pass

            return stats if stats else None
        except Exception as e:
            self.logger.wrn(f"Could not parse stats: {e}")
            return None
