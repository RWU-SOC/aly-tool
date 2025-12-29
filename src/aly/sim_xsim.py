# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Vivado XSIM simulator backend."""

import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional

from aly.backends import SimulatorBackend, SimulationResult
from aly import log


class XsimBackend(SimulatorBackend):
    """Xilinx Vivado XSIM simulator backend."""
    
    def compile(
        self,
        sources: List[Path],
        top: str,
        output_dir: Path,
        includes: List[Path] = None,
        defines: Dict[str, str] = None,
        **kwargs
    ) -> bool:
        """Compile with xvlog."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build xvlog command
        cmd = [self.config.get('vlog', 'xvlog.bat')]
        cmd.append('--sv')  # SystemVerilog
        cmd.extend(['--work', 'work'])
        
        # Add include directories
        if includes:
            for inc in includes:
                cmd.extend(['-i', str(inc)])
        
        # Add defines
        if defines:
            for key, val in defines.items():
                cmd.extend(['-d', f'{key}={val}' if val else key])
        
        # Add sources
        for src in sources:
            cmd.append(str(src))
        
        log.inf(f"Compiling {len(sources)} files with xvlog")
        log.dbg(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=output_dir,
            capture_output=True,
            text=True
        )
        
        # Save log
        log_file = output_dir / 'xvlog.log'
        log_file.write_text(result.stdout + '\n' + result.stderr)
        
        if result.returncode != 0:
            log.err(f"Compilation failed (exit {result.returncode})")
            log.err(f"See {log_file}")
            return False
        
        log.success("Compilation successful")
        return True
    
    def elaborate(
        self,
        top: str,
        output_dir: Path,
        **kwargs
    ) -> bool:
        """Elaborate with xelab."""
        cmd = [self.config.get('xelab', 'xelab.bat')]
        cmd.extend(['--debug', 'typical'])  # Enable debugging
        cmd.extend(['--snapshot', top])
        cmd.append(top)
        
        # Add any extra options
        extra_opts = kwargs.get('elab_opts', [])
        cmd.extend(extra_opts)
        
        log.inf(f"Elaborating {top}")
        log.dbg(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=output_dir,
            capture_output=True,
            text=True
        )
        
        # Save log
        log_file = output_dir / 'xelab.log'
        log_file.write_text(result.stdout + '\n' + result.stderr)
        
        if result.returncode != 0:
            log.err(f"Elaboration failed (exit {result.returncode})")
            log.err(f"See {log_file}")
            return False
        
        log.success("Elaboration successful")
        return True
    
    def simulate(
        self,
        top: str,
        output_dir: Path,
        waves: bool = False,
        gui: bool = False,
        plusargs: List[str] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> SimulationResult:
        """Run simulation with xsim."""
        start_time = time.time()
        
        cmd = [self.config.get('bin', 'xsim.bat')]
        cmd.append(top)  # Snapshot name
        
        if gui:
            cmd.append('--gui')
        else:
            cmd.extend(['--runall'])
        
        # Waveform dump
        waveform_file = None
        if waves:
            waveform_file = output_dir / f'{top}.wdb'
            # XSIM automatically creates .wdb files
        
        # Add plusargs
        if plusargs:
            for arg in plusargs:
                cmd.extend(['--testplusarg', arg])
        
        # Log file
        log_file = output_dir / 'xsim.log'
        cmd.extend(['--log', str(log_file)])
        
        log.inf(f"Running simulation: {top}")
        log.dbg(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            if success:
                log.success(f"Simulation passed ({duration:.2f}s)")
            else:
                log.err(f"Simulation failed (exit {result.returncode})")
            
            return SimulationResult(
                success=success,
                duration=duration,
                log_file=log_file,
                waveform_file=waveform_file if waveform_file and waveform_file.exists() else None,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
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
                stderr="Timeout"
            )
