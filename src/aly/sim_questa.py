# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Questa/ModelSim simulator backend."""

import subprocess
import time
from pathlib import Path
from typing import List, Optional, Dict

from aly import log
from aly.backends import SimulatorBackend, SimulationResult
from aly.workflow_config import WorkflowConfig


class QuestaBackend(SimulatorBackend):
    """Questa/ModelSim simulator backend implementation."""
    
    def __init__(self, config: WorkflowConfig, logger=None):
        """
        Initialize Questa backend.
        
        Args:
            config: Workflow configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or log
        self.tool_config = config.get_tool_config('sim', 'questa')
        
        if not self.tool_config:
            raise ValueError("Questa tool configuration not found in workflow config")
    
    def compile(
        self,
        sources: List[Path],
        top: str,
        output_dir: Path,
        includes: Optional[List[Path]] = None,
        defines: Optional[Dict[str, str]] = None,
        work_lib: str = 'work'
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
            vlib = self.tool_config.get('vlib', 'vlib')
            self.logger.dbg(f"Creating work library: {work_lib}")
            result = subprocess.run(
                [vlib, work_lib],
                cwd=output_dir,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                self.logger.err(f"Failed to create work library: {result.stderr}")
                return False
        
        # Build vlog command
        vlog = self.tool_config.get('vlog', 'vlog')
        cmd = [vlog, '-sv', '-work', work_lib]
        
        # Add include directories
        if includes:
            for inc in includes:
                cmd.extend(['+incdir+' + str(inc)])
        
        # Add defines
        if defines:
            for key, value in defines.items():
                if value:
                    cmd.append(f'+define+{key}={value}')
                else:
                    cmd.append(f'+define+{key}')
        
        # Add lint warnings
        cmd.extend([
            '-lint',
            '-pedanticerrors',
            '-hazards',
        ])
        
        # Add sources
        for src in sources:
            cmd.append(str(src))
        
        # Compile
        log_file = output_dir / f'{top}_vlog.log'
        self.logger.inf(f"Compiling with vlog...")
        self.logger.dbg(f"Command: {' '.join(cmd)}")
        
        with open(log_file, 'w') as f:
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True
            )
        
        if result.returncode != 0:
            self.logger.err(f"Compilation failed. See {log_file}")
            # Print last 20 lines of log
            with open(log_file, 'r') as f:
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
        work_lib: str = 'work',
        timescale: str = '1ns/1ps'
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
        work_lib: str = 'work'
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
        vsim = self.tool_config.get('vsim', 'vsim')
        
        # Build vsim command
        if gui:
            cmd = [vsim, '-gui', f'{work_lib}.{top}']
        else:
            cmd = [vsim, '-batch', '-do', 'run -all; quit', f'{work_lib}.{top}']
        
        # Waveform setup
        waveform_file = None
        if waves:
            waveform_file = output_dir / f'{top}.wlf'
            cmd.extend(['-wlf', str(waveform_file)])
            # Log all signals
            cmd.extend(['-voptargs=+acc'])
        
        # Add plusargs
        if plusargs:
            for arg in plusargs:
                cmd.append(f'+{arg}')
        
        # Run simulation
        log_file = output_dir / f'{top}_sim.log'
        self.logger.inf(f"Running simulation...")
        self.logger.dbg(f"Command: {' '.join(cmd)}")
        
        start_time = time.time()
        success = False
        
        try:
            with open(log_file, 'w') as f:
                result = subprocess.run(
                    cmd,
                    cwd=output_dir,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                    text=True
                )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            if success:
                self.logger.success(f"Simulation completed in {duration:.2f}s")
            else:
                self.logger.err(f"Simulation failed. See {log_file}")
                # Print last 20 lines
                with open(log_file, 'r') as f:
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
        )
