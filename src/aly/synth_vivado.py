# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Vivado synthesis backend."""

import subprocess
import time
from pathlib import Path
from typing import List, Optional, Dict

from aly import log
from aly.backends import SynthesisBackend, SynthesisResult
from aly.workflow_config import WorkflowConfig


class VivadoBackend(SynthesisBackend):
    """Xilinx Vivado synthesis backend."""
    
    def __init__(self, config: WorkflowConfig, logger=None):
        """
        Initialize Vivado backend.
        
        Args:
            config: Workflow configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or log
        self.tool_config = config.get_tool_config('synth', 'vivado')
        
        if not self.tool_config:
            raise ValueError("Vivado tool configuration not found in workflow config")
    
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
        Run Vivado synthesis.
        
        Args:
            sources: List of RTL source files
            top: Top module name
            output_dir: Directory for outputs
            part: FPGA part number (e.g., xc7a100tcsg324-1)
            constraints: XDC constraint files
            includes: Include directories
            defines: Preprocessor defines
            
        Returns:
            SynthesisResult with status and reports
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get part number
        if not part:
            part = self.tool_config.get('part')
        if not part:
            raise ValueError("FPGA part number not specified")
        
        # Generate TCL script
        tcl_script = self._generate_tcl_script(
            sources=sources,
            top=top,
            part=part,
            constraints=constraints,
            includes=includes,
            defines=defines,
            output_dir=output_dir
        )
        
        tcl_file = output_dir / 'synth.tcl'
        with open(tcl_file, 'w') as f:
            f.write(tcl_script)
        
        # Run Vivado in batch mode
        vivado = self.tool_config.get('bin', 'vivado')
        cmd = [
            vivado,
            '-mode', 'batch',
            '-source', str(tcl_file),
            '-log', str(output_dir / 'vivado.log'),
            '-journal', str(output_dir / 'vivado.jou'),
        ]
        
        self.logger.inf("Running Vivado synthesis...")
        self.logger.dbg(f"Command: {' '.join(cmd)}")
        
        start_time = time.time()
        
        result = subprocess.run(
            cmd,
            cwd=output_dir,
            capture_output=True,
            text=True
        )
        
        duration = time.time() - start_time
        success = result.returncode == 0
        
        # Check for timing closure
        timing_met = False
        timing_rpt = output_dir / 'reports' / 'timing_summary.rpt'
        if timing_rpt.exists():
            timing_met = self._check_timing(timing_rpt)
        
        if success:
            if timing_met:
                self.logger.success(f"Synthesis completed in {duration:.2f}s - Timing MET")
            else:
                self.logger.wrn(f"Synthesis completed in {duration:.2f}s - Timing NOT MET")
        else:
            self.logger.err(f"Synthesis failed after {duration:.2f}s")
            self.logger.err(result.stderr)
        
        return SynthesisResult(
            success=success,
            duration=duration,
            reports_dir=output_dir / 'reports',
            timing_met=timing_met
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
            'utilization': 'utilization.rpt',
            'timing': 'timing_summary.rpt',
            'power': 'power.rpt',
            'drc': 'drc.rpt',
        }
        
        for name, filename in report_files.items():
            rpt_path = reports_dir / filename
            if rpt_path.exists():
                reports[name] = rpt_path
        
        return reports
    
    def _generate_tcl_script(
        self,
        sources: List[Path],
        top: str,
        part: str,
        constraints: Optional[List[Path]],
        includes: Optional[List[Path]],
        defines: Optional[Dict[str, str]],
        output_dir: Path
    ) -> str:
        """Generate Vivado TCL synthesis script."""
        
        script = f"""# Vivado Synthesis Script
# Generated by ALY

# Create project
create_project -in_memory -part {part}

# Set properties
set_property target_language Verilog [current_project]
set_property default_lib work [current_project]

"""
        
        # Add source files
        script += "# Add RTL sources\n"
        for src in sources:
            script += f"read_verilog -sv {src}\n"
        
        # Add includes
        if includes:
            script += "\n# Include directories\n"
            for inc in includes:
                script += f"set_property include_dirs {{{inc}}} [current_fileset]\n"
        
        # Add defines
        if defines:
            script += "\n# Defines\n"
            for key, value in defines.items():
                if value:
                    script += f"set_property verilog_define {{{key}={value}}} [current_fileset]\n"
                else:
                    script += f"set_property verilog_define {{{key}}} [current_fileset]\n"
        
        # Add constraints
        if constraints:
            script += "\n# Constraints\n"
            for xdc in constraints:
                script += f"read_xdc {xdc}\n"
        
        # Synthesis
        script += f"""
# Run synthesis
synth_design -top {top} -part {part}

# Create reports directory
file mkdir reports

# Generate reports
report_utilization -file reports/utilization.rpt
report_timing_summary -file reports/timing_summary.rpt
report_power -file reports/power.rpt
report_drc -file reports/drc.rpt

# Write checkpoint
write_checkpoint -force {top}_synth.dcp

# Write netlist
write_verilog -force -mode synth {top}_synth.v

puts "Synthesis complete"
"""
        
        return script
    
    def _check_timing(self, timing_report: Path) -> bool:
        """
        Check if timing is met from timing report.
        
        Args:
            timing_report: Path to timing summary report
            
        Returns:
            True if all timing constraints are met
        """
        try:
            with open(timing_report, 'r') as f:
                content = f.read()
                
                # Look for "All user specified timing constraints are met"
                if "All user specified timing constraints are met" in content:
                    return True
                
                # Check for negative slack
                if "Worst Negative Slack" in content:
                    # Extract WNS value
                    for line in content.split('\n'):
                        if "WNS(ns)" in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == "WNS(ns)" and i + 1 < len(parts):
                                    try:
                                        wns = float(parts[i + 1])
                                        return wns >= 0
                                    except ValueError:
                                        pass
                
                return False
        except Exception as e:
            self.logger.wrn(f"Could not parse timing report: {e}")
            return False
