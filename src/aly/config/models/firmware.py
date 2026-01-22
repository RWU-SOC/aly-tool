# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Firmware manifest classes - self-contained with multi-build support."""

import glob as globlib
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional

from aly.config.models.helpers import (
    FirmwareFlags,
    MemFormat,
    ValidationLevel,
    ValidationMessage,
)


# =============================================================================
# Toolchain - Firmware toolchain configuration
# =============================================================================


@dataclass
class Toolchain:
    """Firmware toolchain configuration.

    Defines a compiler toolchain (e.g., RISC-V GCC, ARM GCC).

    Example YAML (in toolchains.yaml):
    ```yaml
    toolchains:
      riscv32:
        prefix: riscv32-unknown-elf-
        march: rv32imc
        mabi: ilp32
        cflags: [-O2, -g]
        ldflags: [-nostdlib]
    ```
    """

    name: str
    prefix: str = ""
    march: str = ""
    mabi: str = ""
    cpu: str = ""
    cflags: List[str] = field(default_factory=list)
    ldflags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "Toolchain":
        """Create Toolchain from dictionary."""
        return cls(
            name=name,
            prefix=data.get("prefix", f"{name}-"),
            march=data.get("march", ""),
            mabi=data.get("mabi", ""),
            cpu=data.get("cpu", ""),
            cflags=data.get("cflags", []),
            ldflags=data.get("ldflags", []),
        )


# =============================================================================
# OutputSpec - Firmware output format specification
# =============================================================================


@dataclass
class OutputSpec:
    """Firmware output format specification.

    Example YAML:
    ```yaml
    outputs:
      - format: elf

      - format: bin

      - format: mem

        plusarg: MEM_FILE
    ```
    """

    format: str  # "elf" | "bin" | "mem" | "hex" | "lst" | "map" | "disasm" | "coe"
    required: bool = True
    plusarg: Optional[str] = None  # For mem files used in simulation

    @classmethod
    def from_dict(cls, data: Any) -> "OutputSpec":
        """Create OutputSpec from dictionary or string."""
        if isinstance(data, str):
            return cls(format=data, required=True)
        return cls(
            format=data.get("format", "elf"),
            required=data.get("required", True),
            plusarg=data.get("plusarg"),
        )

    @classmethod
    def from_list(cls, data: List[Any]) -> List["OutputSpec"]:
        """Parse a list of output specifications."""
        result = []
        for item in data or []:
            result.append(cls.from_dict(item))
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        d: Dict[str, Any] = {"format": self.format, "required": self.required}
        if self.plusarg:
            d["plusarg"] = self.plusarg
        return d


# =============================================================================
# FirmwareBuild - Single build in a collection
# =============================================================================


@dataclass
class FirmwareBuild:
    """A single firmware build within a collection.

    Self-contained class with no inheritance or helper dependencies.
    Uses plain dicts for nested structures.

    Example YAML:
    ```yaml
    builds:
      - name: bootloader
        author: "Mohamed Aly"
        version: "1.0.0"
        languages: [asm, c]
        sources:
          - src/boot.S
          - src/main.c
          - src/boot/*.s
        includes:
          - include
          - common/include
        linker_script: linkers/memory.ld
        toolchain: riscv64
        flags:
          common: [-fno-builtin, -nostdlib]
          c: [-O2, -Wall]
          asm: [-x]
          ld: [-nostartfiles]
        outputs:
          - format: elf
          - format: mem
        mem:
          - name: memory.mem
            word_width: 64
            byte_order: little
    ```
    """

    name: str
    author: str = ""
    version: str = "1.0.0"
    languages: List[str] = field(default_factory=lambda: ["c"])

    # Build-specific sources
    sources: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    linker_script: Optional[str] = None
    defines: Dict[str, str] = field(default_factory=dict)

    # Toolchain override (per-build)
    toolchain: Optional[str] = None

    # Compiler/linker flags
    flags: FirmwareFlags = field(default_factory=FirmwareFlags)

    # Output formats
    outputs: List[OutputSpec] = field(default_factory=list)

    # Memory file formats
    mem: List[MemFormat] = field(default_factory=list)

    # Internal tracking
    _manifest_path: Optional[Path] = field(default=None, repr=False)

    @property
    def root_dir(self) -> Optional[Path]:
        """Get the directory containing the manifest."""
        if self._manifest_path:
            return self._manifest_path.parent
        return None

    def resolve_path(self, path: str) -> Path:
        """Resolve a path relative to manifest location."""
        p = Path(path)
        if p.is_absolute():
            return p
        if self.root_dir:
            return (self.root_dir / p).resolve()
        return p.resolve()

    def resolve_files(self) -> List[Path]:
        """Resolve source paths and expand glob patterns.

        Returns:
            List of resolved Path objects for all matching files.
        """
        resolved = []
        if not self.root_dir:
            return resolved

        for file_pattern in self.sources:
            pattern_path = self.root_dir / file_pattern
            # Check if it's a glob pattern
            if "*" in file_pattern or "?" in file_pattern:
                matches = sorted(globlib.glob(str(pattern_path), recursive=True))
                for match in matches:
                    p = Path(match)
                    if p.exists() and p.is_file() and p not in resolved:
                        resolved.append(p)
            else:
                # Direct file path
                if pattern_path.exists() and pattern_path.is_file():
                    if pattern_path not in resolved:
                        resolved.append(pattern_path)

        return resolved

    def get_source_files(self) -> List[Path]:
        """Get resolved source file paths (supports globs).

        Alias for resolve_files() for API consistency.
        """
        return self.resolve_files()

    def get_include_dirs(self) -> List[Path]:
        """Get resolved include directories."""
        includes = []
        for inc in self.includes:
            p = self.resolve_path(inc)
            if p.exists() and p.is_dir():
                includes.append(p)
        return includes

    def get_linker_script(self) -> Optional[Path]:
        """Get resolved linker script path."""
        if self.linker_script:
            return self.resolve_path(self.linker_script)
        return None

    def get_all_cflags(self) -> List[str]:
        """Get all C compiler flags (common + c)."""
        flags = list(self.flags.common)
        flags.extend(self.flags.c)
        return flags

    def get_all_ldflags(self) -> List[str]:
        """Get all linker flags (common + ld)."""
        flags = list(self.flags.common)
        flags.extend(self.flags.ld)
        return flags

    def get_asm_flags(self) -> List[str]:
        """Get assembler flags (common + asm)."""
        flags = list(self.flags.common)
        flags.extend(self.flags.asm)
        return flags

    def get_required_outputs(self) -> List[OutputSpec]:
        """Get list of required output formats."""
        return [out for out in self.outputs if out.required]

    def needs_format(self, format_name: str) -> bool:
        """Check if a specific output format is needed."""
        return any(out.format == format_name for out in self.outputs)

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], manifest_path: Optional[Path] = None
    ) -> "FirmwareBuild":
        """Create FirmwareBuild from dictionary."""
        return cls(
            name=data.get("name", "unnamed"),
            author=data.get("author", ""),
            version=data.get("version", "1.0.0"),
            languages=data.get("languages", ["c"]),
            sources=data.get("sources", []),
            includes=data.get("includes", []),
            linker_script=data.get("linker_script"),
            defines=data.get("defines", {}),
            toolchain=data.get("toolchain"),
            flags=FirmwareFlags.from_dict(data.get("flags", {})),
            outputs=OutputSpec.from_list(data.get("outputs", [])),
            mem=MemFormat.from_list(data.get("mem", [])),
            _manifest_path=manifest_path,
        )

    @classmethod
    def from_list(
        cls, data: List[Dict[str, Any]], manifest_path: Optional[Path] = None
    ) -> List["FirmwareBuild"]:
        """Create list of FirmwareBuilds from list of dictionaries."""
        return [cls.from_dict(item, manifest_path) for item in (data or [])]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        d: Dict[str, Any] = {
            "name": self.name,
        }
        if self.author:
            d["author"] = self.author
        if self.version != "1.0.0":
            d["version"] = self.version
        if self.languages != ["c"]:
            d["languages"] = self.languages
        if self.sources:
            d["sources"] = self.sources
        if self.includes:
            d["includes"] = self.includes
        if self.linker_script:
            d["linker_script"] = self.linker_script
        if self.defines:
            d["defines"] = self.defines
        if self.toolchain:
            d["toolchain"] = self.toolchain
        if self.flags.common or self.flags.c or self.flags.asm or self.flags.ld:
            d["flags"] = {
                "common": self.flags.common,
                "c": self.flags.c,
                "asm": self.flags.asm,
                "ld": self.flags.ld,
            }
        if self.outputs:
            d["outputs"] = [o.to_dict() for o in self.outputs]
        if self.mem:
            d["mem"] = [
                {
                    "name": m.name,
                    "format": m.format,
                    "word_width": m.word_width,
                    "byte_order": m.byte_order,
                }
                for m in self.mem
            ]
        return d


# =============================================================================
# FirmwareManifest - Firmware manifest with multi-build support
# =============================================================================


@dataclass
class FirmwareManifest:
    """Firmware manifest - self-contained, supports multiple builds.

    Self-contained class for managing firmware manifests with 'builds:' list.
    Uses standard manifest.yaml format for ProjectConfig discovery.

    Example manifest (manifest.yaml):
    ```yaml
    name: my_firmware
    type: firmware
    version: 1.0.0
    description: Firmware for my SoC
    author: Mohamed Aly
    license: Apache-2.0

    # Global default toolchain (can be overridden per-build)
    toolchain: riscv64

    # Build definitions
    builds:
      - name: bootloader
        author: Mohamed Aly
        version: 1.0.0
        languages: [asm, c]
        sources:
          - src/boot.S
          - src/main.c
        includes: [include]
        linker_script: linkers/memory.ld
        flags:
          common: [-fno-builtin, -nostdlib]
          c: [-O2, -Wall]
          asm: [-x]
          ld: [-nostartfiles]
        outputs:
          - format: elf
          - format: mem
        mem:
          - name: memory.mem
            word_width: 64
            byte_order: little

      - name: application
        sources:
          - src/app/main.c
        # ... other fields
    ```
    """

    # Top-level manifest metadata
    name: str = "firmware"
    type: str = "firmware"
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = ""

    # Global default toolchain (can be overridden per-build)
    toolchain: str = ""

    # Build list
    builds: List[FirmwareBuild] = field(default_factory=list)

    # Internal
    _manifest_path: Optional[Path] = field(default=None, repr=False)

    @property
    def root_dir(self) -> Optional[Path]:
        """Get the directory containing the manifest."""
        if self._manifest_path:
            return self._manifest_path.parent
        return None

    def resolve_path(self, path: str) -> Path:
        """Resolve a path relative to manifest location."""
        p = Path(path)
        if p.is_absolute():
            return p
        if self.root_dir:
            return (self.root_dir / p).resolve()
        return p.resolve()

    def get_build(self, name: str) -> Optional[FirmwareBuild]:
        """Get a build by name."""
        for build in self.builds:
            if build.name == name:
                return build
        return None

    def add_build(self, build: FirmwareBuild) -> bool:
        """Add a build to the collection.

        Returns:
            True if added, False if build with same name exists.
        """
        if self.get_build(build.name):
            return False
        build._manifest_path = self._manifest_path
        self.builds.append(build)
        return True

    def get_builds(
        self, builds: Optional[List[FirmwareBuild]] = None
    ) -> List[FirmwareBuild]:
        """Get all builds in this manifest.

        If `builds` is provided, append into it (avoiding duplicates by name).
        Otherwise, create and return a new list.
        """
        if builds is None:
            builds = []

        seen_names = {b.name for b in builds}

        for build in self.builds:
            if build.name not in seen_names:
                builds.append(build)
                seen_names.add(build.name)

        return builds

    def get_build_names(self, names: Optional[List[str]] = None) -> List[str]:
        """Get all build names.

        If `names` is provided, append into it (avoiding duplicates).
        Otherwise, create and return a new list.
        """
        if names is None:
            names = []

        seen = set(names)

        for build in self.builds:
            if build.name not in seen:
                names.append(build.name)
                seen.add(build.name)

        return names

    def validate(self) -> List[ValidationMessage]:
        """Validate the manifest."""
        messages = []

        if not self.name:
            messages.append(
                ValidationMessage(
                    level=ValidationLevel.ERROR,
                    message="Manifest requires a 'name' field",
                    file=self._manifest_path,
                    field="name",
                )
            )

        if not self.builds:
            messages.append(
                ValidationMessage(
                    level=ValidationLevel.WARNING,
                    message="Manifest has no builds defined",
                    file=self._manifest_path,
                    field="builds",
                )
            )

        # Validate each build
        for build in self.builds:
            if not build.name:
                messages.append(
                    ValidationMessage(
                        level=ValidationLevel.ERROR,
                        message="Build requires a 'name' field",
                        file=self._manifest_path,
                        field="builds",
                    )
                )

            if not build.sources:
                messages.append(
                    ValidationMessage(
                        level=ValidationLevel.ERROR,
                        message=f"Build '{build.name}' requires at least one source file",
                        file=self._manifest_path,
                        field=f"builds[{build.name}].sources",
                    )
                )

            # Validate output formats
            valid_formats = {"elf", "bin", "mem", "hex", "lst", "map", "disasm", "coe"}
            for output in build.outputs:
                if output.format not in valid_formats:
                    messages.append(
                        ValidationMessage(
                            level=ValidationLevel.WARNING,
                            message=f"Unknown output format in build '{build.name}': {output.format}",
                            file=self._manifest_path,
                            field=f"builds[{build.name}].outputs",
                        )
                    )

        return messages

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], manifest_path: Optional[Path] = None
    ) -> "FirmwareManifest":
        """Create FirmwareManifest from dictionary."""
        builds = FirmwareBuild.from_list(data.get("builds", []), manifest_path)

        return cls(
            name=data.get("name", "firmware"),
            type=data.get("type", "firmware"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            license=data.get("license", ""),
            toolchain=data.get("toolchain", ""),
            builds=builds,
            _manifest_path=manifest_path,
        )

    @classmethod
    def load(cls, manifest_path: Path) -> "FirmwareManifest":
        """Load manifest from a YAML file."""
        if not manifest_path.exists():
            raise FileNotFoundError(f"Firmware manifest not found: {manifest_path}")

        try:
            with open(manifest_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {manifest_path}: {e}")

        return cls.from_dict(data, manifest_path)

    def save(self, manifest_path: Optional[Path] = None):
        """Save manifest to a YAML file."""
        path = manifest_path or self._manifest_path
        if not path:
            raise ValueError("No manifest path specified")

        data: Dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "version": self.version,
        }

        # Add optional metadata
        if self.description:
            data["description"] = self.description
        if self.author:
            data["author"] = self.author
        if self.license:
            data["license"] = self.license
        if self.toolchain:
            data["toolchain"] = self.toolchain

        # Add builds (IMPORTANT: serialize to dicts)
        data["builds"] = [b.to_dict() for b in self.builds]

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        self._manifest_path = path

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        data: Dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "version": self.version,
        }
        if self.description:
            data["description"] = self.description
        if self.author:
            data["author"] = self.author
        if self.license:
            data["license"] = self.license
        if self.toolchain:
            data["toolchain"] = self.toolchain

        # IMPORTANT: builds as list of dicts
        data["builds"] = [b.to_dict() for b in self.builds]

        return data
