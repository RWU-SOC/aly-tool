# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Helper classes used across different manifest types."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum


@dataclass
class RTLPackage:
    """Package entry with optional name and module scoping.

    Packages can have an optional `name` for referencing as dependencies.
    If `modules` is empty, the package applies to all modules in the manifest.
    Otherwise, it applies only to the listed module names.

    Example YAML:
    ```yaml
    packages:
      - name: common_pkg
        path: pkg/common_pkg.sv
        modules: []  # applies to all modules

      - name: cpu_types_pkg
        path: pkg/cpu_types_pkg.sv
        modules: [cpu]  # only for cpu module
    ```
    """
    path: str
    name: Optional[str] = None
    modules: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to YAML-friendly dict."""
        d: dict = {"path": self.path}
        if self.name:
            d["name"] = self.name
        if self.modules:
            d["modules"] = self.modules
        return d


# HDL Language constants
class HDLLanguage:
    """Supported HDL languages and their file extensions."""

    SYSTEMVERILOG = "systemverilog"
    VERILOG = "verilog"
    VHDL = "vhdl"

    ALL = [SYSTEMVERILOG, VERILOG, VHDL]

    EXTENSIONS = {
        SYSTEMVERILOG: [".sv", ".svh"],
        VERILOG: [".v", ".vh"],
        VHDL: [".vhd", ".vhdl"],
    }

    @classmethod
    def get_extensions(cls, language: str) -> List[str]:
        """Get file extensions for a language."""
        return cls.EXTENSIONS.get(language, [".sv", ".v"])

    @classmethod
    def is_valid(cls, language: str) -> bool:
        """Check if language is valid."""
        return language in cls.ALL

    DISPLAY_NAMES = {
        "systemverilog": "SystemVerilog",
        "verilog": "Verilog",
        "vhdl": "VHDL",
    }

    @classmethod
    def get_display_name(cls, language: str) -> str:
        """Get display name for a language."""
        return cls.DISPLAY_NAMES.get(language, language)


class ValidationLevel(Enum):
    """Validation message severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationMessage:
    """Structured validation message with context."""

    level: ValidationLevel
    message: str
    file: Optional[Path] = None
    line: Optional[int] = None
    field: Optional[str] = None

    def __str__(self) -> str:
        """Format validation message for display."""
        parts = [f"[{self.level.value.upper()}]"]
        if self.file:
            parts.append(f"{self.file}")
            if self.line:
                parts[1] += f":{self.line}"
        if self.field:
            parts.append(f"field '{self.field}'")
        parts.append(self.message)
        return " ".join(parts)




@dataclass
class FirmwareFlags:
    """Compiler flags for firmware builds.

    Example YAML:
    ```yaml
    flags:
      common: [-fno-builtin, -nostdlib]
      c: [-O2, -Wall]
      asm: [-x, assembler-with-cpp]
      ld: [-nostartfiles]
    ```
    """

    common: List[str] = field(default_factory=list)
    c: List[str] = field(default_factory=list)
    asm: List[str] = field(default_factory=list)
    ld: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FirmwareFlags":
        """Create FirmwareFlags from dictionary."""
        if not data:
            return cls()
        return cls(
            common=data.get("common", []),
            c=data.get("c", []),
            asm=data.get("asm", []),
            ld=data.get("ld", []),
        )


@dataclass
class MemFormat:
    """Memory file format specification.

    Example YAML:
    ```yaml
    mem:
      - name: memory_le.mem
        format: mem
        word_width: 64
        byte_order: little
        fill: 0x00000013
    ```
    """

    name: str
    format: str = "mem"  # "mem" | "hex" | "bin" | "coe"
    word_width: int = 32
    byte_order: str = "little"  # "little" | "big"
    fill: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemFormat":
        """Create MemFormat from dictionary."""
        fill = data.get("fill", 0)
        if isinstance(fill, str):
            fill = int(fill, 16) if fill.startswith("0x") else int(fill)

        return cls(
            name=data.get("name", "memory.mem"),
            format=data.get("format", "mem"),
            word_width=data.get("word_width", 32),
            byte_order=data.get("byte_order", "little"),
            fill=fill,
        )

    @classmethod
    def from_list(cls, data: List[Dict[str, Any]]) -> List["MemFormat"]:
        """Parse a list of memory formats."""
        result = []
        for item in data or []:
            if isinstance(item, dict):
                result.append(cls.from_dict(item))
        return result
