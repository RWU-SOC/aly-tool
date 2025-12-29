# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Abstract base classes for simulation and synthesis backends."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SimulationResult:
    """Result of a simulation run."""
    success: bool
    duration: float  # seconds
    log_file: Path
    waveform_file: Optional[Path] = None
    coverage_file: Optional[Path] = None
    return_code: int = 0
    stdout: str = ""
    stderr: str = ""


@dataclass
class SynthesisResult:
    """Result of a synthesis run."""
    success: bool
    duration: float
    reports_dir: Path
    timing_met: Optional[bool] = None
    area: Optional[Dict[str, int]] = None
    return_code: int = 0


class SimulatorBackend(ABC):
    """Abstract base class for simulator backends."""
    
    def __init__(self, config: Dict[str, Any], project_root: Path):
        self.config = config
        self.project_root = project_root
        self.name = self.__class__.__name__.replace('Backend', '').lower()
    
    @abstractmethod
    def compile(
        self,
        sources: List[Path],
        top: str,
        output_dir: Path,
        includes: List[Path] = None,
        defines: Dict[str, str] = None,
        **kwargs
    ) -> bool:
        """Compile RTL sources.
        
        Args:
            sources: List of source files
            top: Top module name
            output_dir: Output directory for compilation
            includes: Include directories
            defines: Preprocessor defines
            
        Returns:
            True if compilation successful
        """
        pass
    
    @abstractmethod
    def elaborate(
        self,
        top: str,
        output_dir: Path,
        **kwargs
    ) -> bool:
        """Elaborate the design.
        
        Args:
            top: Top module name
            output_dir: Output directory
            
        Returns:
            True if elaboration successful
        """
        pass
    
    @abstractmethod
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
        """Run simulation.
        
        Args:
            top: Top module name
            output_dir: Output directory
            waves: Enable waveform dump
            gui: Open GUI
            plusargs: Simulation plusargs
            timeout: Simulation timeout in seconds
            
        Returns:
            SimulationResult with status and outputs
        """
        pass


class SynthesisBackend(ABC):
    """Abstract base class for synthesis backends."""
    
    def __init__(self, config: Dict[str, Any], project_root: Path):
        self.config = config
        self.project_root = project_root
        self.name = self.__class__.__name__.replace('Backend', '').lower()
    
    @abstractmethod
    def synthesize(
        self,
        sources: List[Path],
        top: str,
        output_dir: Path,
        constraints: Optional[Path] = None,
        target: Optional[str] = None,
        **kwargs
    ) -> SynthesisResult:
        """Run synthesis.
        
        Args:
            sources: List of source files
            top: Top module name
            output_dir: Output directory
            constraints: Constraints file (SDC/XDC)
            target: Target device/technology
            
        Returns:
            SynthesisResult with reports
        """
        pass
    
    @abstractmethod
    def get_reports(self, output_dir: Path) -> Dict[str, Path]:
        """Get synthesis reports.
        
        Args:
            output_dir: Output directory
            
        Returns:
            Dictionary mapping report type to file path
        """
        pass
