# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""RTL and IP manifest classes - self-contained, no inheritance."""

import fnmatch
import glob as globlib
import yaml
from dataclasses import dataclass, field
from aly.config.models.helpers import HDLLanguage, ValidationLevel, ValidationMessage
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterable



# =============================================================================
# IPManifest - Vendor IP block manifest (standalone)
# =============================================================================


@dataclass
class IPManifest:
    """Vendor IP block manifest - self-contained, no inheritance.

    Represents vendor-provided IP with optional precompiled simulation models.
    Supports nested manifests for RTL, testbench, and firmware components.

    Example: ip/uart/manifest.yaml
    ```yaml
    name: uart_ip
    type: ip
    version: 1.0.0
    vendor: xilinx
    license: Proprietary

    language: systemverilog

    # Direct file listing (simple IP)
    files:
      - rtl/uart.sv
      - rtl/uart_core.sv

    # OR use nested manifests (complex IP)
    # rtl_manifest: rtl/manifest.yaml
    # tb_manifest: tb/manifest.yaml
    # fw_manifest: fw/manifest.yaml

    binaries:
      simulation: models/uart_sim.o

    compatibility:
      tools: [xsim, questa]
      languages: [systemverilog]

    parameters:
      BAUD_RATE: 115200
      DATA_WIDTH: 8

    interfaces:
      - name: tx
        direction: output
        width: 1
    ```
    """

    # Required
    name: str
    type: str = "ip"

    # Metadata
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = ""
    vendor: str = ""
    language: str = "systemverilog"

    # Source files (optional - may use binaries instead)
    files: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    defines: Dict[str, str] = field(default_factory=dict)

    # Precompiled simulation models
    binaries: Dict[str, str] = field(default_factory=dict)

    # Tool compatibility
    compatibility: Dict[str, Any] = field(default_factory=dict)

    # Design metadata
    parameters: Dict[str, Any] = field(default_factory=dict)
    interfaces: List[Dict[str, Any]] = field(default_factory=list)

    # Discovery metadata
    discoverable: bool = True
    maintainers: List[Dict[str, str]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    namespace: Optional[str] = None

    # Internal manifest paths (for nested IP structure)
    rtl_manifest: Optional[str] = None
    tb_manifest: Optional[str] = None
    fw_manifest: Optional[str] = None

    # Internal
    _manifest_path: Optional[Path] = field(default=None, repr=False)

    @property
    def root_dir(self) -> Optional[Path]:
        """Get the directory containing this manifest."""
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

    def validate(self) -> List[ValidationMessage]:
        """Validate IP manifest configuration."""
        messages = []

        # Required fields
        if not self.name:
            messages.append(
                ValidationMessage(
                    level=ValidationLevel.ERROR,
                    message="Manifest requires a 'name' field",
                    file=self._manifest_path,
                    field="name",
                )
            )

        # Validate type
        if self.type != "ip":
            messages.append(
                ValidationMessage(
                    level=ValidationLevel.WARNING,
                    message=f"Type should be 'ip', got '{self.type}'",
                    file=self._manifest_path,
                    field="type",
                )
            )

        # Must have either files, binaries, or internal manifests
        has_internal = (
            self.rtl_manifest is not None
            or self.tb_manifest is not None
            or self.fw_manifest is not None
            or (self.root_dir and (self.root_dir / "rtl" / "manifest.yaml").exists())
        )
        if not self.files and not self.binaries and not has_internal:
            messages.append(
                ValidationMessage(
                    level=ValidationLevel.ERROR,
                    message="IP manifest must have 'files', 'binaries', or internal manifests",
                    file=self._manifest_path,
                    field="files",
                )
            )

        # Vendor recommended
        if not self.vendor:
            messages.append(
                ValidationMessage(
                    level=ValidationLevel.WARNING,
                    message="IP manifest should specify 'vendor'",
                    file=self._manifest_path,
                    field="vendor",
                )
            )

        # Validate file existence
        for f in self.files:
            resolved = self.resolve_path(f)
            if not resolved.exists():
                messages.append(
                    ValidationMessage(
                        level=ValidationLevel.ERROR,
                        message=f"File not found: {f}",
                        file=self._manifest_path,
                        field="files",
                    )
                )

        # Validate binaries exist
        for bin_type, bin_path in self.binaries.items():
            resolved = self.resolve_path(bin_path)
            if not resolved.exists():
                messages.append(
                    ValidationMessage(
                        level=ValidationLevel.ERROR,
                        message=f"Binary not found: {bin_path}",
                        file=self._manifest_path,
                        field=f"binaries.{bin_type}",
                    )
                )

        return messages

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], manifest_path: Optional[Path] = None
    ) -> "IPManifest":
        """Create IPManifest from dictionary."""
        return cls(
            name=data.get("name", "ip"),
            type=data.get("type", "ip"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            license=data.get("license", ""),
            vendor=data.get("vendor", ""),
            language=data.get("language", "systemverilog"),
            files=data.get("files", []),
            includes=data.get("includes", []),
            defines=data.get("defines", {}),
            binaries=data.get("binaries", {}),
            compatibility=data.get("compatibility", {}),
            parameters=data.get("parameters", {}),
            interfaces=data.get("interfaces", []),
            discoverable=data.get("discoverable", True),
            maintainers=data.get("maintainers", []),
            tags=data.get("tags", []),
            namespace=data.get("namespace"),
            rtl_manifest=data.get("rtl_manifest"),
            tb_manifest=data.get("tb_manifest"),
            fw_manifest=data.get("fw_manifest"),
            _manifest_path=manifest_path,
        )

    @classmethod
    def load(cls, manifest_path: Path) -> "IPManifest":
        """Load manifest from a YAML file."""
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        try:
            with open(manifest_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {manifest_path}: {e}")

        manifest = cls.from_dict(data, manifest_path)

        # Run validation
        messages = manifest.validate()
        errors = [m for m in messages if m.level == ValidationLevel.ERROR]

        if errors:
            error_text = "\n".join(str(e) for e in errors)
            raise ValueError(
                f"Manifest validation failed for {manifest_path}:\n{error_text}"
            )

        return manifest

    def get_rtl_files(self) -> List[Path]:
        """Get RTL source files (if available)."""
        files = []
        for f in self.files:
            p = self.resolve_path(f)
            if p.exists():
                files.append(p)
        return files

    def get_include_dirs(self) -> List[Path]:
        """Get include directories."""
        includes = []
        for inc in self.includes:
            p = self.resolve_path(inc)
            if p.exists():
                includes.append(p)
        return includes

    def has_simulation_model(self) -> bool:
        """Check if IP has precompiled simulation model."""
        return "simulation" in self.binaries

    # =========================================================================
    # Internal Manifest Support
    # =========================================================================

    def has_internal_manifests(self) -> bool:
        """Check if IP has nested manifests (rtl/, tb/, fw/ subdirectories)."""
        if not self.root_dir:
            return False
        return (
            (self.root_dir / "rtl" / "manifest.yaml").exists()
            or (self.root_dir / "tb" / "manifest.yaml").exists()
            or (self.root_dir / "fw" / "manifest.yaml").exists()
            or self.rtl_manifest is not None
            or self.tb_manifest is not None
            or self.fw_manifest is not None
        )

    def get_rtl_manifest(self) -> Optional["RTLManifest"]:
        """Load internal RTL manifest.

        Tries explicit rtl_manifest path first, then auto-detects rtl/manifest.yaml.

        Returns:
            RTLManifest if found, None otherwise
        """
        from aly.config.models.rtl import RTLManifest

        manifest_path = None

        # Try explicit path first
        if self.rtl_manifest:
            manifest_path = self.resolve_path(self.rtl_manifest)
        # Auto-detect standard location
        elif self.root_dir:
            auto_path = self.root_dir / "rtl" / "manifest.yaml"
            if auto_path.exists():
                manifest_path = auto_path

        if manifest_path and manifest_path.exists():
            return RTLManifest.load(manifest_path)
        return None

    def get_testbench_manifest(self) -> Optional["TestbenchManifest"]:
        """Load internal testbench manifest.

        Tries explicit tb_manifest path first, then auto-detects tb/manifest.yaml.

        Returns:
            TestbenchManifest if found, None otherwise
        """
        from aly.config.models.testbench import TestbenchManifest

        manifest_path = None

        # Try explicit path first
        if self.tb_manifest:
            manifest_path = self.resolve_path(self.tb_manifest)
        # Auto-detect standard location
        elif self.root_dir:
            auto_path = self.root_dir / "tb" / "manifest.yaml"
            if auto_path.exists():
                manifest_path = auto_path

        if manifest_path and manifest_path.exists():
            return TestbenchManifest.load(manifest_path)
        return None

    def get_firmware_manifest(self) -> Optional["FirmwareManifest"]:
        """Load internal firmware manifest.

        Tries explicit fw_manifest path first, then auto-detects fw/manifest.yaml.

        Returns:
            FirmwareManifest if found, None otherwise
        """
        from aly.config.models.firmware import FirmwareManifest

        manifest_path = None

        # Try explicit path first
        if self.fw_manifest:
            manifest_path = self.resolve_path(self.fw_manifest)
        # Auto-detect standard location
        elif self.root_dir:
            auto_path = self.root_dir / "fw" / "manifest.yaml"
            if auto_path.exists():
                manifest_path = auto_path

        if manifest_path and manifest_path.exists():
            return FirmwareManifest.load(manifest_path)
        return None

    def get_rtl_modules(self) -> List[Any]:
        """Get RTL modules from internal manifest.

        Returns:
            List of RTLModule objects, or empty list if no RTL manifest
        """
        rtl = self.get_rtl_manifest()
        return rtl.modules if rtl else []

    def get_testbenches(self) -> List[Any]:
        """Get testbenches from internal manifest.

        Returns:
            List of Testbench objects, or empty list if no TB manifest
        """
        tb = self.get_testbench_manifest()
        return tb.testbenches if tb else []


# Type hints for forward references
RTLManifest = Any
TestbenchManifest = Any
FirmwareManifest = Any
