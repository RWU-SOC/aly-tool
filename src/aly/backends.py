# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Abstract base classes for simulation and synthesis backends."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass


# =============================================================================
# Tool Language Support Registry
# =============================================================================


class ToolLanguageSupport:
    """Registry of supported languages for each tool."""

    # Simulator language support
    SIMULATORS = {
        "xsim": {"systemverilog", "verilog", "vhdl"},
        "questa": {"systemverilog", "verilog", "vhdl"},
        "modelsim": {"systemverilog", "verilog", "vhdl"},
        "verilator": {"systemverilog", "verilog"},  # No VHDL support
        "iverilog": {"verilog"},  # Limited SystemVerilog, no VHDL
        "vcs": {"systemverilog", "verilog"},
        "xcelium": {"systemverilog", "verilog", "vhdl"},
    }

    # Synthesizer language support
    SYNTHESIZERS = {
        "vivado": {"systemverilog", "verilog", "vhdl"},
        "quartus": {"systemverilog", "verilog", "vhdl"},
        "yosys": {"systemverilog", "verilog"},  # VHDL via GHDL plugin only
        "synplify": {"systemverilog", "verilog", "vhdl"},
        "dc": {"systemverilog", "verilog", "vhdl"},  # Design Compiler
        "genus": {"systemverilog", "verilog", "vhdl"},  # Cadence Genus
    }

    # Linter language support
    LINTERS = {
        "verilator": {"systemverilog", "verilog"},
        "spyglass": {"systemverilog", "verilog", "vhdl"},
        "hal": {"systemverilog", "verilog"},
        "slang": {"systemverilog", "verilog"},
    }

    @classmethod
    def get_simulator_languages(cls, tool: str) -> Set[str]:
        """Get supported languages for a simulator."""
        return cls.SIMULATORS.get(tool.lower(), set())

    @classmethod
    def get_synthesizer_languages(cls, tool: str) -> Set[str]:
        """Get supported languages for a synthesizer."""
        return cls.SYNTHESIZERS.get(tool.lower(), set())

    @classmethod
    def get_linter_languages(cls, tool: str) -> Set[str]:
        """Get supported languages for a linter."""
        return cls.LINTERS.get(tool.lower(), set())

    @classmethod
    def simulator_supports(cls, tool: str, language: str) -> bool:
        """Check if simulator supports a language."""
        return language.lower() in cls.get_simulator_languages(tool)

    @classmethod
    def synthesizer_supports(cls, tool: str, language: str) -> bool:
        """Check if synthesizer supports a language."""
        return language.lower() in cls.get_synthesizer_languages(tool)

    @classmethod
    def linter_supports(cls, tool: str, language: str) -> bool:
        """Check if linter supports a language."""
        return language.lower() in cls.get_linter_languages(tool)


class UnsupportedLanguageError(Exception):
    """Raised when a tool does not support the project's HDL language."""

    def __init__(self, tool: str, language: str, supported: Set[str]):
        self.tool = tool
        self.language = language
        self.supported = supported
        supported_str = ", ".join(sorted(supported)) if supported else "none"
        super().__init__(
            f"Tool '{tool}' does not support '{language}'. "
            f"Supported languages: {supported_str}"
        )


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


@dataclass
class FirmwareResult:
    """Result of a firmware build."""

    success: bool
    duration: float  # seconds
    build_name: str
    elf_file: Optional[Path] = None
    bin_file: Optional[Path] = None
    mem_files: Dict[str, Path] = None  # format -> path mapping
    lst_file: Optional[Path] = None
    return_code: int = 0
    stdout: str = ""
    stderr: str = ""

    def __post_init__(self):
        if self.mem_files is None:
            self.mem_files = {}


class SimulatorBackend(ABC):
    """Abstract base class for simulator backends."""

    def __init__(self, config: Dict[str, Any], project_root: Path):
        self.config = config
        self.project_root = project_root
        self.name = self.__class__.__name__.replace("Backend", "").lower()

    @abstractmethod
    def compile(
        self,
        sources: List[Path],
        top: str,
        output_dir: Path,
        includes: List[Path] = None,
        defines: Dict[str, str] = None,
        **kwargs,
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
    def elaborate(self, top: str, output_dir: Path, **kwargs) -> bool:
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
        **kwargs,
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
        self.name = self.__class__.__name__.replace("Backend", "").lower()

    @abstractmethod
    def synthesize(
        self,
        sources: List[Path],
        top: str,
        output_dir: Path,
        constraints: Optional[Path] = None,
        target: Optional[str] = None,
        **kwargs,
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


class FirmwareBackend(ABC):
    """Abstract base class for firmware build backends.

    Firmware backends compile C/ASM sources into executables and
    generate memory initialization files for simulation.

    Typical workflow:
        1. Instantiate backend with toolchain config
        2. Call build() with build configuration
        3. Result contains paths to ELF, binary, and memory files
    """

    def __init__(self, config: Dict[str, Any], project_root: Path):
        """Initialize firmware backend.

        Args:
            config: Toolchain configuration (prefix, march, mabi, etc.)
            project_root: Project root directory
        """
        self.config = config
        self.project_root = project_root
        self.name = self.__class__.__name__.replace("Backend", "").lower()

    @abstractmethod
    def check_toolchain(self) -> bool:
        """Check if the toolchain is available.

        Returns:
            True if toolchain executables are found
        """
        pass

    @abstractmethod
    def build(
        self,
        build_config: Any,  # FirmwareBuildConfig from models
        output_dir: Path,
        mem_formats: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> FirmwareResult:
        """Build firmware from sources.

        Args:
            build_config: Firmware build configuration (sources, linker, etc.)
            output_dir: Output directory for build artifacts
            mem_formats: List of memory format configurations, each containing:
                - format: Output format (hex, mem, coe, verilog, bin)
                - word_width: Word width in bits (8, 16, 32, 64)
                - byte_order: Byte order ('little' or 'big')
                - plusarg: Optional plusarg name for simulation

        Returns:
            FirmwareResult with paths to generated files
        """
        pass

    def get_prefix(self) -> str:
        """Get toolchain prefix (e.g., 'riscv64-unknown-elf-')."""
        return self.config.get("prefix", "")

    @staticmethod
    def generate_mem_file(
        bin_file: Path,
        output_file: Path,
        format: str = "mem",
        word_width: int = 32,
        byte_order: str = "little",
    ) -> bool:
        """Generate memory initialization file from binary.

        This is a utility method that can be used by all firmware backends.

        Args:
            bin_file: Input binary file
            output_file: Output memory file
            format: Output format (hex, mem, coe, verilog, bin)
            word_width: Word width in bits (8, 16, 32, 64)
            byte_order: Byte order ('little' or 'big')

        Returns:
            True if generation successful
        """
        try:
            with open(bin_file, "rb") as f:
                data = f.read()

            word_bytes = word_width // 8

            # Pad data to word boundary
            remainder = len(data) % word_bytes
            if remainder:
                padding = word_bytes - remainder
                data += b"\x00" * padding

            # Convert to words
            words = []
            for i in range(0, len(data), word_bytes):
                word_data = data[i : i + word_bytes]
                if byte_order == "little":
                    word = int.from_bytes(word_data, "little")
                else:
                    word = int.from_bytes(word_data, "big")
                words.append(word)

            # Write in specified format
            hex_digits = word_width // 4

            if format == "hex":
                with open(output_file, "w") as f:
                    for word in words:
                        f.write(f"{word:0{hex_digits}x}\n")

            elif format == "mem":
                with open(output_file, "w") as f:
                    f.write("// Memory initialization file\n")
                    f.write(f"// {len(words)} words, {word_width} bits each\n")
                    f.write("@0\n")
                    for word in words:
                        f.write(f"{word:0{hex_digits}x}\n")

            elif format == "coe":
                with open(output_file, "w") as f:
                    f.write("; Memory initialization file for Xilinx\n")
                    f.write("memory_initialization_radix=16;\n")
                    f.write("memory_initialization_vector=\n")
                    for i, word in enumerate(words):
                        sep = "," if i < len(words) - 1 else ";"
                        f.write(f"{word:0{hex_digits}x}{sep}\n")

            elif format == "verilog":
                with open(output_file, "w") as f:
                    f.write("// Verilog memory array initialization\n")
                    f.write(f"// {len(words)} words, {word_width} bits each\n")
                    f.write(
                        f"logic [{word_width - 1}:0] mem [0:{len(words) - 1}] = '{{\n"
                    )
                    for i, word in enumerate(words):
                        sep = "," if i < len(words) - 1 else ""
                        f.write(f"    {word_width}'h{word:0{hex_digits}x}{sep}\n")
                    f.write("};\n")

            elif format == "bin":
                with open(output_file, "wb") as f:
                    f.write(data)

            return True

        except Exception:
            return False
