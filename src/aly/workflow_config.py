# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""RTL workflow configuration management."""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class RTLConfig:
    """RTL source configuration."""
    top: str
    dirs: List[str]
    includes: List[str] = field(default_factory=list)
    defines: Dict[str, str] = field(default_factory=dict)


@dataclass
class TestbenchConfig:
    """Testbench configuration."""
    root: str
    tops: Dict[str, Dict[str, str]]  # name -> {filelist, ...}


@dataclass
class ToolConfig:
    """Tool-specific configuration."""
    bin: str
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimToolsConfig:
    """Simulation tools configuration."""
    xsim: Optional[ToolConfig] = None
    questa: Optional[ToolConfig] = None
    xcelium: Optional[ToolConfig] = None
    verilator: Optional[ToolConfig] = None


@dataclass
class SynthToolsConfig:
    """Synthesis tools configuration."""
    vivado: Optional[ToolConfig] = None
    yosys: Optional[ToolConfig] = None
    genus: Optional[ToolConfig] = None


@dataclass
class FirmwareConfig:
    """Firmware build configuration."""
    build_dir: str = "build/fw"
    cmake_options: List[str] = field(default_factory=list)
    make_options: List[str] = field(default_factory=list)


@dataclass
class WorkflowConfig:
    """Complete workflow configuration."""
    rtl: RTLConfig
    tb: TestbenchConfig
    tools: Dict[str, Any]
    fw: FirmwareConfig
    project_root: Path
    
    @classmethod
    def load(cls, config_path: Path, project_root: Path) -> 'WorkflowConfig':
        """Load configuration from YAML file."""
        with open(config_path) as f:
            data = yaml.safe_load(f)
        
        # Parse RTL config
        rtl_data = data.get('rtl', {})
        rtl = RTLConfig(
            top=rtl_data.get('top', 'top'),
            dirs=rtl_data.get('dirs', []),
            includes=rtl_data.get('includes', []),
            defines=rtl_data.get('defines', {})
        )
        
        # Parse testbench config
        tb_data = data.get('tb', {})
        tb = TestbenchConfig(
            root=tb_data.get('root', 'tb'),
            tops=tb_data.get('tops', {})
        )
        
        # Parse firmware config
        fw_data = data.get('fw', {})
        fw = FirmwareConfig(
            build_dir=fw_data.get('build_dir', 'build/fw'),
            cmake_options=fw_data.get('cmake_options', []),
            make_options=fw_data.get('make_options', [])
        )
        
        return cls(
            rtl=rtl,
            tb=tb,
            tools=data.get('tools', {}),
            fw=fw,
            project_root=project_root
        )
    
    def resolve_path(self, path: str) -> Path:
        """Resolve path relative to project root."""
        p = Path(path)
        if p.is_absolute():
            return p
        return (self.project_root / p).resolve()
    
    def get_rtl_files(self) -> List[Path]:
        """Get all RTL source files."""
        files = []
        for dir_path in self.rtl.dirs:
            rtl_dir = self.resolve_path(dir_path)
            if rtl_dir.exists():
                files.extend(rtl_dir.rglob('*.sv'))
                files.extend(rtl_dir.rglob('*.v'))
        return files
    
    def get_sim_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get simulator tool configuration."""
        sim_tools = self.tools.get('sim', {})
        return sim_tools.get(tool_name)
    
    def get_synth_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get synthesis tool configuration."""
        synth_tools = self.tools.get('synth', {})
        return synth_tools.get(tool_name)
