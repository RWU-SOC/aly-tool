# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Yosys open-source synthesis backend."""

import subprocess
import time
import json
from pathlib import Path
from typing import List, Optional, Dict

from aly import log
from aly.backends import SynthesisBackend, SynthesisResult
from aly.workflow_config import WorkflowConfig


class YosysBackend(SynthesisBackend):
    """Yosys open-source synthesis backend."""
    
    def __init__(self, config: WorkflowConfig, logger=None):
        """
        Initialize Yosys backend.
        
        Args:
            config: Workflow configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or log
        self.tool_config = config.get_tool_config('synth', 'yosys')
        
        if not self.tool_config:
            raise ValueError("Yosys tool configuration not found in workflow config")
    
    def synthesize(
        self,
        sources: List[Path],
        top: str,
        output_dir: Path,
        part: Optional[str] = None,
        constraints: Optional[List[Path]] = None,
        includes: Optional[List[Path]] = None,
        defines: Optional[Dict[str, str]] = None,
    ) -> SynthesisResult:
        """
        Run Yosys synthesis.
        
        Args:
            sources: List of RTL source files
            top: Top module name
            output_dir: Directory for outputs
            part: Technology library (e.g., 'sky130', 'asap7')
            constraints: SDC constraint files (not all tools support)
            includes: Include directories
            defines: Preprocessor defines
            
        Returns:
            SynthesisResult with status and reports
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        reports_dir = output_dir / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        # Get technology
        tech = part or self.tool_config.get('tech', 'generic')
        
        # Generate Yosys script
        script = self._generate_yosys_script(
            sources=sources,
            top=top,
            tech=tech,
            includes=includes,
            defines=defines,
            output_dir=output_dir
        )
        
        script_file = output_dir / 'synth.ys'
        with open(script_file, 'w') as f:
            f.write(script)
        
        # Run Yosys
        yosys = self.tool_config.get('bin', 'yosys')
        cmd = [yosys, '-s', str(script_file)]
        
        log_file = output_dir / 'yosys.log'
        self.logger.inf("Running Yosys synthesis...")
        self.logger.dbg(f"Command: {' '.join(cmd)}")
        
        start_time = time.time()
        
        with open(log_file, 'w') as f:
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True
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
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    self.logger.err(line.rstrip())
        
        return SynthesisResult(
            success=success,
            duration=duration,
            reports_dir=reports_dir,
            timing_met=None  # Yosys doesn't do timing analysis by default
        )
    
    def get_reports(self, output_dir: Path) -> Dict[str, Path]:
        """
        Get paths to synthesis reports.
        
        Args:
            output_dir: Synthesis output directory
            
        Returns:
            Dictionary of report name to file path
        """
        reports_dir = output_dir / 'reports'
        if not reports_dir.exists():
            return {}
        
        reports = {}
        report_files = {
            'stats': 'stats.txt',
            'check': 'check.txt',
            'hierarchy': 'hierarchy.txt',
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
        output_dir: Path
    ) -> str:
        """Generate Yosys synthesis script."""
        
        script = f"""# Yosys Synthesis Script
# Generated by ALY

"""
        
        # Read sources
        script += "# Read RTL sources\n"
        
        # Build read_verilog command with options
        read_opts = ["-sv"]
        
        if includes:
            for inc in includes:
                read_opts.append(f"-I{inc}")
        
        if defines:
            for key, value in defines.items():
                if value:
                    read_opts.append(f"-D{key}={value}")
                else:
                    read_opts.append(f"-D{key}")
        
        for src in sources:
            script += f"read_verilog {' '.join(read_opts)} {src}\n"
        
        # Hierarchy
        script += f"\n# Set top module and hierarchy\n"
        script += f"hierarchy -check -top {top}\n"
        script += "hierarchy -check > reports/hierarchy.txt\n"
        
        # Synthesis based on technology
        script += f"\n# Synthesis for {tech}\n"
        
        if tech == 'generic':
            # Generic synthesis
            script += """# Generic synthesis flow
proc
opt
fsm
opt
memory
opt
techmap
opt
"""
        elif 'sky130' in tech.lower():
            # SkyWater 130nm
            script += """# Sky130 synthesis flow
synth -top {top}
dfflibmap -liberty sky130_fd_sc_hd__tt_025C_1v80.lib
abc -liberty sky130_fd_sc_hd__tt_025C_1v80.lib
""".format(top=top)
        elif 'ice40' in tech.lower():
            # Lattice iCE40
            script += f"synth_ice40 -top {top}\n"
        elif 'ecp5' in tech.lower():
            # Lattice ECP5
            script += f"synth_ecp5 -top {top}\n"
        else:
            # Default generic flow
            script += f"synth -top {top}\n"
        
        # Reports and outputs
        script += """
# Generate reports
stat > reports/stats.txt
check > reports/check.txt

# Write outputs
write_verilog -noattr synth.v
write_json synth.json

# Done
"""
        
        return script
    
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
            with open(log_file, 'r') as f:
                content = f.read()
                
                # Look for "Number of cells" line
                for line in content.split('\n'):
                    if 'Number of cells:' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            try:
                                stats['num_cells'] = int(parts[1].strip())
                            except ValueError:
                                pass
                    elif 'Number of wires:' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            try:
                                stats['num_wires'] = int(parts[1].strip())
                            except ValueError:
                                pass
            
            return stats if stats else None
        except Exception as e:
            self.logger.wrn(f"Could not parse stats: {e}")
            return None
