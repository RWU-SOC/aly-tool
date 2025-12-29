# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Verilator simulator backend."""

import subprocess
import time
from pathlib import Path
from typing import List, Optional, Dict

from aly import log
from aly.backends import SimulatorBackend, SimulationResult
from aly.workflow_config import WorkflowConfig


class VerilatorBackend(SimulatorBackend):
    """Verilator simulator backend (compile to C++ executable)."""
    
    def __init__(self, config: WorkflowConfig, logger=None):
        """
        Initialize Verilator backend.
        
        Args:
            config: Workflow configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or log
        self.tool_config = config.get_tool_config('sim', 'verilator')
        
        if not self.tool_config:
            raise ValueError("Verilator tool configuration not found in workflow config")
    
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
        
        verilator = self.tool_config.get('bin', 'verilator')
        
        # Build verilator command
        cmd = [
            verilator,
            '--cc',  # Generate C++ output
            '--exe',  # Create executable
            '--build',  # Build immediately
            '-Wall',  # Enable all warnings
            '--top-module', top,
            '-Mdir', str(output_dir / 'obj_dir'),
        ]
        
        # Add trace support if requested
        trace = self.tool_config.get('trace', True)
        if trace:
            cmd.extend([
                '--trace',  # Enable VCD tracing
                '--trace-structs',  # Trace structs
            ])
        
        # Add coverage if requested
        coverage = self.tool_config.get('coverage', False)
        if coverage:
            cmd.append('--coverage')
        
        # Add include directories
        if includes:
            for inc in includes:
                cmd.extend(['-I' + str(inc)])
        
        # Add defines
        if defines:
            for key, value in defines.items():
                if value:
                    cmd.append(f'-D{key}={value}')
                else:
                    cmd.append(f'-D{key}')
        
        # Add C++ testbench if exists
        tb_cpp = output_dir.parent.parent / 'tb' / f'{top}.cpp'
        if tb_cpp.exists():
            cmd.append(str(tb_cpp))
            self.logger.dbg(f"Using C++ testbench: {tb_cpp}")
        else:
            # Need to create minimal testbench
            self.logger.wrn("No C++ testbench found, simulation will require manual driver")
        
        # Add sources
        for src in sources:
            cmd.append(str(src))
        
        # Compile
        log_file = output_dir / f'{top}_verilator.log'
        self.logger.inf(f"Compiling with Verilator...")
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
            self.logger.err(f"Verilator compilation failed. See {log_file}")
            # Print last 30 lines of log
            with open(log_file, 'r') as f:
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
        work_lib: str = 'work',
        timescale: str = '1ns/1ps'
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
        exe_path = output_dir / 'obj_dir' / f'V{top}'
        if exe_path.exists() or (exe_path.with_suffix('.exe').exists()):
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
        work_lib: str = 'work'
    ) -> SimulationResult:
        """
        Run Verilator-compiled executable.
        
        Args:
            top: Top module name to simulate
            output_dir: Directory with compiled executable
            waves: Enable waveform dumping
            gui: Ignored for Verilator (use GTKWave separately)
            plusargs: Additional plusargs to pass to simulator
            timeout: Simulation timeout in seconds
            work_lib: Work library name (unused)
            
        Returns:
            SimulationResult with status and outputs
        """
        # Find executable
        exe_path = output_dir / 'obj_dir' / f'V{top}'
        if not exe_path.exists():
            exe_path = exe_path.with_suffix('.exe')  # Windows
        
        if not exe_path.exists():
            self.logger.err(f"Verilator executable not found: {exe_path}")
            return SimulationResult(
                success=False,
                duration=0.0,
                log_file=output_dir / f'{top}_sim.log',
                waveform_file=None
            )
        
        # Build command
        cmd = [str(exe_path)]
        
        # Waveform setup
        waveform_file = None
        if waves:
            waveform_file = output_dir / f'{top}.vcd'
            cmd.append(f'+trace')
            # Verilator testbench should handle VCD output
        
        # Add plusargs
        if plusargs:
            for arg in plusargs:
                cmd.append(f'+{arg}')
        
        # Run simulation
        log_file = output_dir / f'{top}_sim.log'
        self.logger.inf(f"Running Verilator simulation...")
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
        
        if gui and waveform_file and waveform_file.exists():
            # Launch GTKWave
            try:
                subprocess.Popen(['gtkwave', str(waveform_file)])
                self.logger.inf("Launched GTKWave for waveform viewing")
            except FileNotFoundError:
                self.logger.wrn("GTKWave not found, view waveform manually")
        
        return SimulationResult(
            success=success,
            duration=duration,
            log_file=log_file,
            waveform_file=waveform_file if waveform_file and waveform_file.exists() else None
        )
