# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Tool configuration classes for simulation, synthesis, lint, constraints, and FPGA."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional


# =============================================================================
# Simulation Configuration
# =============================================================================


@dataclass
class SimToolConfig:
    """Single simulator tool configuration."""

    name: str
    bin: str
    vlog: Optional[str] = None
    xelab: Optional[str] = None
    vsim: Optional[str] = None
    vvp: Optional[str] = None
    compile_opts: List[str] = field(default_factory=list)
    elab_opts: List[str] = field(default_factory=list)
    run_opts: List[str] = field(default_factory=list)
    gui_opts: List[str] = field(default_factory=list)
    args: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "SimToolConfig":
        return cls(
            name=name,
            bin=data.get("bin", name),
            vlog=data.get("vlog"),
            xelab=data.get("xelab"),
            vsim=data.get("vsim"),
            vvp=data.get("vvp"),
            compile_opts=data.get("compile_opts", []),
            elab_opts=data.get("elab_opts", []),
            run_opts=data.get("run_opts", []),
            gui_opts=data.get("gui_opts", []),
            args=data.get("args", []),
        )


@dataclass
class SimConfig:
    """Simulation configuration."""

    default_tool: str = "xsim"
    language: str = "systemverilog"
    build_dir: str = "build/sim"
    tools: Dict[str, SimToolConfig] = field(default_factory=dict)
    waves: bool = False
    coverage: bool = False
    verbosity: str = "normal"
    _project_root: Optional[Path] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], project_root: Path) -> "SimConfig":
        tools = {}
        for name, tool_data in (data.get("tools") or {}).items():
            if isinstance(tool_data, dict):
                tools[name] = SimToolConfig.from_dict(name, tool_data)

        return cls(
            default_tool=data.get("default_tool", "xsim"),
            language=data.get("language", "systemverilog"),
            build_dir=data.get("build_dir", "build/sim"),
            tools=tools,
            waves=data.get("waves", False),
            coverage=data.get("coverage", False),
            verbosity=data.get("verbosity", "normal"),
            _project_root=project_root,
        )

    def get_tool(self, name: str) -> Optional[SimToolConfig]:
        """Get simulator tool by name."""
        return self.tools.get(name)

    def get_default_tool(self) -> Optional[SimToolConfig]:
        """Get the default simulator tool."""
        return self.tools.get(self.default_tool)

    def get_build_dir(self) -> Path:
        """Get simulation build directory."""
        if self._project_root is None:
            return Path(self.build_dir)
        return self._project_root / self.build_dir


# =============================================================================
# Synthesis Configuration
# =============================================================================


@dataclass
class CellLibrary:
    """Cell library configuration for ASIC synthesis.

    Example YAML:
    ```yaml
    libraries:
      sky130_hd:
        liberty: libs/sky130_fd_sc_hd__tt_025C_1v80.lib
        verilog: libs/sky130_fd_sc_hd.v
        lef: libs/sky130_fd_sc_hd.lef
        description: Sky130 HD standard cells
    ```
    """

    name: str
    liberty: str  # Path to liberty (.lib) file
    verilog: Optional[str] = None  # Path to Verilog models
    lef: Optional[str] = None  # Path to LEF file
    description: str = ""

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "CellLibrary":
        return cls(
            name=name,
            liberty=data.get("liberty", ""),
            verilog=data.get("verilog"),
            lef=data.get("lef"),
            description=data.get("description", ""),
        )


@dataclass
class SynthToolConfig:
    """Single synthesis tool configuration.

    Example YAML:
    ```yaml
    tools:
      vivado:
        bin: vivado
        threads: 8
        batch_opts:
          - "-mode"
          - "batch"

      yosys:
        bin: yosys
        script_ext: ".ys"
        tech: generic
        liberty: libs/mycells.lib  # For ASIC flow
    ```
    """

    name: str
    bin: str
    batch_opts: List[str] = field(default_factory=list)
    script_ext: str = ".tcl"
    threads: int = 1
    # Yosys-specific
    tech: str = "generic"
    liberty: Optional[str] = None
    # Vivado-specific
    part: Optional[str] = None

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "SynthToolConfig":
        return cls(
            name=name,
            bin=data.get("bin", name),
            batch_opts=data.get("batch_opts", []),
            script_ext=data.get("script_ext", ".tcl" if name != "yosys" else ".ys"),
            threads=data.get("threads", data.get("thread", 1)),
            tech=data.get("tech", "generic"),
            liberty=data.get("liberty"),
            part=data.get("part"),
        )


@dataclass
class SynthTargetConfig:
    """Single synthesis target.

    Example YAML:
    ```yaml
    targets:
      arty_a7:
        tool: vivado
        part: xc7a100tcsg324-1
        top: fpga_top
        constraints:
          - constraints/arty_a7.xdc
        options:
          strategy: "Flow_PerfOptimized_high"

      asic_sky130:
        tool: yosys
        tech: sky130
        library: sky130_hd
        top: chip_top
        constraints:
          - constraints/timing.sdc
    ```
    """

    name: str
    tool: str
    part: str = ""
    tech: str = "generic"
    library: Optional[str] = None  # Reference to cell library name
    top: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "SynthTargetConfig":
        constraints = data.get("constraints", [])
        if isinstance(constraints, str):
            constraints = [constraints]
        return cls(
            name=name,
            tool=data.get("tool", "vivado"),
            part=data.get("part", ""),
            tech=data.get("tech", "generic"),
            library=data.get("library"),
            top=data.get("top"),
            constraints=constraints,
            options=data.get("options", {}),
        )


@dataclass
class SynthConfig:
    """Synthesis configuration.

    Example YAML (.aly/synth.yaml):
    ```yaml
    default_tool: vivado
    build_dir: build/synth

    # Cell libraries for ASIC synthesis
    libraries:
      sky130_hd:
        liberty: libs/sky130_fd_sc_hd__tt_025C_1v80.lib
        verilog: libs/sky130_fd_sc_hd.v

    # Tool configurations
    tools:
      vivado:
        bin: vivado
        threads: 8
      yosys:
        bin: yosys
        tech: generic

    # Synthesis targets
    targets:
      arty_a7:
        tool: vivado
        part: xc7a100tcsg324-1
        top: fpga_top

    # Global options
    options:
      reports:
        - utilization
        - timing
        - power
    ```
    """

    default_tool: str = "vivado"
    build_dir: str = "build/synth"
    libraries: Dict[str, CellLibrary] = field(default_factory=dict)
    tools: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    targets: Dict[str, SynthTargetConfig] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    _project_root: Optional[Path] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], project_root: Path) -> "SynthConfig":
        # Parse cell libraries
        libraries = {}
        for name, lib_data in (data.get("libraries") or {}).items():
            if isinstance(lib_data, dict):
                libraries[name] = CellLibrary.from_dict(name, lib_data)

        # Parse targets
        targets = {}
        for name, target_data in (data.get("targets") or {}).items():
            if isinstance(target_data, dict):
                targets[name] = SynthTargetConfig.from_dict(name, target_data)

        return cls(
            default_tool=data.get("default_tool", "vivado"),
            build_dir=data.get("build_dir", "build/synth"),
            libraries=libraries,
            tools=data.get("tools", {}),
            targets=targets,
            options=data.get("options", {}),
            _project_root=project_root,
        )

    def get_target(self, name: str) -> Optional[SynthTargetConfig]:
        """Get synthesis target by name."""
        return self.targets.get(name)

    def get_tool_config(self, name: str) -> Dict[str, Any]:
        """Get tool configuration as dict.

        This returns the raw dict for backends that expect Dict[str, Any].
        """
        return self.tools.get(name, {})

    def get_library(self, name: str) -> Optional[CellLibrary]:
        """Get cell library by name."""
        return self.libraries.get(name)

    def get_liberty_path(self, library_name: str) -> Optional[Path]:
        """Get resolved liberty file path for a library."""
        lib = self.get_library(library_name)
        if not lib or not lib.liberty:
            return None
        return self._resolve_path(lib.liberty)

    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to project root."""
        p = Path(path)
        if p.is_absolute():
            return p
        if self._project_root:
            return (self._project_root / p).resolve()
        return p

    def get_build_dir(self) -> Path:
        """Get synthesis build directory."""
        if self._project_root is None:
            return Path(self.build_dir)
        return self._project_root / self.build_dir


# =============================================================================
# Lint Configuration
# =============================================================================


@dataclass
class LintToolConfig:
    """Single lint tool configuration."""

    name: str
    bin: str
    args: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "LintToolConfig":
        return cls(
            name=name,
            bin=data.get("bin", name),
            args=data.get("args", []),
        )


@dataclass
class LintRules:
    """Lint rules configuration."""

    categories: Dict[str, bool] = field(default_factory=dict)
    enable: List[str] = field(default_factory=list)
    disable: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LintRules":
        return cls(
            categories=data.get("categories", {}),
            enable=data.get("enable", []),
            disable=data.get("disable", []),
        )


@dataclass
class LintConfig:
    """Lint configuration."""

    default_tool: str = "verilator"
    severity: str = "warning"
    tools: Dict[str, LintToolConfig] = field(default_factory=dict)
    rules: LintRules = field(default_factory=LintRules)
    waivers: List[str] = field(default_factory=list)
    _project_root: Optional[Path] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], project_root: Path) -> "LintConfig":
        tools = {}
        for name, tool_data in (data.get("tools") or {}).items():
            if isinstance(tool_data, dict):
                tools[name] = LintToolConfig.from_dict(name, tool_data)

        return cls(
            default_tool=data.get("default_tool", "verilator"),
            severity=data.get("severity", "warning"),
            tools=tools,
            rules=LintRules.from_dict(data.get("rules", {})),
            waivers=data.get("waivers", []),
            _project_root=project_root,
        )

    def get_tool(self, name: str) -> Optional[LintToolConfig]:
        """Get linter tool configuration."""
        return self.tools.get(name)

    def get_default_tool(self) -> Optional[LintToolConfig]:
        """Get the default linter tool."""
        return self.tools.get(self.default_tool)

    def is_waived(self, path: str) -> bool:
        """Check if a path is waived from linting."""
        from fnmatch import fnmatch

        for pattern in self.waivers:
            if fnmatch(path, pattern):
                return True
        return False


# =============================================================================
# Constraints Configuration
# =============================================================================


@dataclass
class ConstraintSet:
    """Single constraint set definition."""

    target: str  # FPGA part number
    files: List[str]
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConstraintSet":
        return cls(
            target=data.get("target", ""),
            files=data.get("files", []),
            description=data.get("description", ""),
        )


@dataclass
class ClockConstraint:
    """Clock definition for constraints."""

    period: float  # ns
    waveform: List[float]
    pin: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClockConstraint":
        return cls(
            period=data.get("period", 10.0),
            waveform=data.get("waveform", [0.0, 5.0]),
            pin=data.get("pin", ""),
        )


@dataclass
class IODefaults:
    """Default I/O standards."""

    standard: str = "LVCMOS33"
    drive: int = 12
    slew: str = "SLOW"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IODefaults":
        if not data:
            return cls()
        return cls(
            standard=data.get("standard", "LVCMOS33"),
            drive=data.get("drive", 12),
            slew=data.get("slew", "SLOW"),
        )


@dataclass
class ConstraintsConfig:
    """Design constraints configuration."""

    default_target: str = ""
    sets: Dict[str, ConstraintSet] = field(default_factory=dict)
    boards: Dict[str, str] = field(default_factory=dict)
    clocks: Dict[str, ClockConstraint] = field(default_factory=dict)
    io_defaults: IODefaults = field(default_factory=IODefaults)
    _project_root: Optional[Path] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], project_root: Path) -> "ConstraintsConfig":
        sets = {}
        for name, set_data in (data.get("sets") or {}).items():
            if isinstance(set_data, dict):
                sets[name] = ConstraintSet.from_dict(set_data)

        clocks = {}
        for name, clk_data in (data.get("clocks") or {}).items():
            if isinstance(clk_data, dict):
                clocks[name] = ClockConstraint.from_dict(clk_data)

        return cls(
            default_target=data.get("default_target", ""),
            sets=sets,
            boards=data.get("boards", {}),
            clocks=clocks,
            io_defaults=IODefaults.from_dict(data.get("io_defaults", {})),
            _project_root=project_root,
        )

    def resolve_path(self, path: str) -> Path:
        """Resolve path relative to project root."""
        p = Path(path)
        if p.is_absolute():
            return p
        if self._project_root:
            return (self._project_root / p).resolve()
        return p

    def get_constraint_files(self, target: Optional[str] = None) -> List[Path]:
        """Get constraint files for a target."""
        target = target or self.default_target
        if not target or target not in self.sets:
            return []

        files = []
        for f in self.sets[target].files:
            p = self.resolve_path(f)
            if p.exists():
                files.append(p)
        return files


# =============================================================================
# FPGA Configuration
# =============================================================================


@dataclass
class FPGAConfig:
    """FPGA programming configuration."""

    default_board: str = ""
    boards: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _project_root: Optional[Path] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], project_root: Path) -> "FPGAConfig":
        return cls(
            default_board=data.get("default_board", ""),
            boards=data.get("boards", {}),
            _project_root=project_root,
        )

    def get_board(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get board configuration by name."""
        board_name = name or self.default_board
        return self.boards.get(board_name, {})
