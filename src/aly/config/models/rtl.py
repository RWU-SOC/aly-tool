# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""RTL manifest classes - self-contained"""

import glob as globlib
import yaml
from dataclasses import dataclass, field
from aly.config.models.helpers import (
    RTLPackage,
    HDLLanguage,
    ValidationLevel,
    ValidationMessage,
)
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterable


# =============================================================================
# RTLModule - Single module in a collection
# =============================================================================


@dataclass
class RTLModule:
    """A single RTL module within a collection.

    Self-contained class with no inheritance or helper dependencies.
    Uses plain dicts for nested structures.

    Example YAML:
    ```yaml
    modules:
      - name: cpu
        author: "John Doe"
        version: "1.0.0"
        language: systemverilog
        files:
          - cpu.sv
          - alu.sv
        dependencies:
          - name: periph
            type: rtl

    ```
    """

    name: str
    author: str = ""
    top: Optional[str] = None
    version: str = "1.0.0"
    language: str = "systemverilog"
    files: List[str] = field(default_factory=list)
    dependencies: List[Dict[str, Any]] = field(default_factory=list)

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
        """Resolve file paths and expand glob patterns.

        Returns:
            List of resolved Path objects for all matching files.
        """
        resolved = []
        if not self.root_dir:
            return resolved

        for file_pattern in self.files:
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

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], manifest_path: Optional[Path] = None
    ) -> "RTLModule":
        """Create RTLModule from dictionary."""
        # Parse dependencies as plain dicts
        deps = []
        for dep in data.get("dependencies", []):
            if isinstance(dep, str):
                deps.append({"name": dep, "type": "rtl", "required": True})
            elif isinstance(dep, dict):
                deps.append(dep)

        return cls(
            name=data.get("name", "unnamed"),
            author=data.get("author", ""),
            top=data.get("top"),
            version=data.get("version", "1.0.0"),
            language=data.get("language", "systemverilog"),
            files=data.get("files", []),
            dependencies=deps,
            _manifest_path=manifest_path,
        )

    @classmethod
    def from_list(
        cls, data: List[Dict[str, Any]], manifest_path: Optional[Path] = None
    ) -> List["RTLModule"]:
        """Create list of RTLModules from list of dictionaries."""
        return [cls.from_dict(item, manifest_path) for item in (data or [])]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        data: Dict[str, Any] = {
            "name": self.name,
            "author": self.author,
            "version": self.version,
            "language": self.language,
            "files": self.files,
            "dependencies": self.dependencies,
        }
        if self.top:
            data["top"] = self.top
        return data


# =============================================================================
# RTLManifest - RTL manifest with multi-module support
# =============================================================================


@dataclass
class RTLManifest:
    """RTL manifest - self-contained, supports multiple modules.

    Self-contained class for managing RTL manifests with optional 'modules:' list.
    Uses standard manifest.yaml format for ProjectConfig discovery.

    Example manifest (manifest.yaml):
    ```yaml
    name: my_rtl_design
    type: rtl
    version: 1.0.0
    description: My RTL design with CPU and peripherals
    author: Mohamed Aly
    license: Apache-2.0
    vendor: my_company
    language: systemverilog

    # Top module reference (module name from modules list)
    top: cpu

    # Shared packages (compiled first, available to all modules)
    packages:
      - pkg/types_pkg.sv
      - pkg/config_pkg.sv

    # Shared include directories
    includes:
      - include
      - common/include

    # Shared defines
    defines:
      SYNTHESIS: ""
      DEBUG_LEVEL: "2"

    # Module definitions
    modules:
      - name: cpu
        author: Mohamed Aly
        version: 1.0.0
        language: systemverilog
        top: cpu_top
        files:
          - rtl/cpu/cpu_top.sv
          - rtl/cpu/alu.sv
          - rtl/cpu/regfile.sv
        dependencies:
          - name: periph
            type: rtl


      - name: periph
        author: Mohamed Aly
        version: 0.5.0
        language: systemverilog
        top: periph_top
        files:
          - rtl/periph/uart.sv
          - rtl/periph/gpio.sv
          - rtl/periph/periph_top.sv
        dependencies: []
    ```
    """

    # Top-level manifest metadata
    name: str = "rtl"
    type: str = "rtl"
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = ""
    vendor: str = ""
    language: str = "systemverilog"

    # Top module reference (name of a module in modules list)
    top: Optional[str] = None

    # Shared source files (available to all modules)
    packages: List[RTLPackage] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    defines: Dict[str, str] = field(default_factory=dict)

    # Module list
    modules: List[RTLModule] = field(default_factory=list)

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

    def get_module(self, name: str) -> Optional[RTLModule]:
        """Get a module by name."""
        for module in self.modules:
            if module.name == name:
                return module
        return None

    def get_package(self, name: str) -> Optional[RTLPackage]:
        """Get a package by name."""
        for pkg in self.packages:
            if pkg.name == name:
                return pkg
        return None

    def get_package_names(self) -> List[str]:
        """Get all named package names."""
        return [pkg.name for pkg in self.packages if pkg.name]

    def get_top_module(self) -> Optional[RTLModule]:
        """Get the top-level module."""
        if self.top:
            return self.get_module(self.top)
        # Default to first module if no top specified
        return self.modules[0] if self.modules else None

    def add_module(self, module: RTLModule) -> bool:
        """Add a module to the collection.

        Returns:
            True if added, False if module with same name exists.
        """
        if self.get_module(module.name):
            return False
        module._manifest_path = self._manifest_path
        self.modules.append(module)
        return True

    def add_files_to_module(self, module_name: str, files: List[str]) -> bool:
        """Add files or patterns to a module's file list."""
        module = self.get_module(module_name)
        if not module:
            return False

        for file_pattern in files:
            if file_pattern not in module.files:
                module.files.append(file_pattern)
        return True

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

        # Validate language
        if not HDLLanguage.is_valid(self.language):
            messages.append(
                ValidationMessage(
                    level=ValidationLevel.ERROR,
                    message=f"Invalid language: {self.language}. "
                    f"Must be one of: {', '.join(HDLLanguage.ALL)}",
                    file=self._manifest_path,
                    field="language",
                )
            )

        if not self.modules:
            messages.append(
                ValidationMessage(
                    level=ValidationLevel.WARNING,
                    message="Manifest has no modules defined",
                    file=self._manifest_path,
                    field="modules",
                )
            )

        # Validate top module reference
        if self.top and not self.get_module(self.top):
            messages.append(
                ValidationMessage(
                    level=ValidationLevel.ERROR,
                    message=f"Top module '{self.top}' not found in modules list",
                    file=self._manifest_path,
                    field="top",
                )
            )

        # Validate package files exist
        for pkg in self.packages:
            resolved = self.resolve_path(pkg.path)
            if not resolved.exists():
                messages.append(
                    ValidationMessage(
                        level=ValidationLevel.ERROR,
                        message=f"Package file not found: {pkg.path}",
                        file=self._manifest_path,
                        field="packages",
                    )
                )

        # Validate include directories exist
        for inc_path in self.includes:
            resolved = self.resolve_path(inc_path)
            if not resolved.exists() or not resolved.is_dir():
                messages.append(
                    ValidationMessage(
                        level=ValidationLevel.WARNING,
                        message=f"Include directory not found: {inc_path}",
                        file=self._manifest_path,
                        field="includes",
                    )
                )

        return messages

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], manifest_path: Optional[Path] = None
    ) -> "RTLManifest":
        """Create RTLManifest from dictionary."""
        modules = RTLModule.from_list(data.get("modules", []), manifest_path)

        # Parse packages with optional module scoping
        raw_pkgs = data.get("packages", [])
        packages: List[RTLPackage] = []

        for item in raw_pkgs:
            if not isinstance(item, dict):
                raise ValueError(
                    "Invalid package entry: expected mapping with 'path' "
                    "and optional 'name'/'modules' fields"
                )
            path = item.get("path")
            if not path:
                raise ValueError("Package entry missing 'path' field")
            name = item.get("name")
            modules_scope = item.get("modules", [])
            if isinstance(modules_scope, str):
                modules_scope = [modules_scope]
            packages.append(RTLPackage(path=path, name=name, modules=modules_scope))

        return cls(
            name=data.get("name", "rtl"),
            type=data.get("type", "rtl"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            license=data.get("license", ""),
            vendor=data.get("vendor", ""),
            language=data.get("language", "systemverilog"),
            top=data.get("top"),
            packages=packages,
            includes=data.get("includes", []),
            defines=data.get("defines", {}),
            modules=modules,
            _manifest_path=manifest_path,
        )

    @classmethod
    def load(cls, manifest_path: Path) -> "RTLManifest":
        """Load manifest from a YAML file."""
        if not manifest_path.exists():
            raise FileNotFoundError(f"RTL manifest not found: {manifest_path}")

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
        if self.vendor:
            data["vendor"] = self.vendor
        if self.language != "systemverilog":
            data["language"] = self.language

        # Add top module reference
        if self.top:
            data["top"] = self.top

        # Add shared resources
        if self.packages:
            data["packages"] = [pkg.to_dict() for pkg in self.packages]
        if self.includes:
            data["includes"] = self.includes
        if self.defines:
            data["defines"] = self.defines

        # Add modules (IMPORTANT: serialize to dicts)
        data["modules"] = [m.to_dict() for m in self.modules]

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        self._manifest_path = path

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        data: Dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "language": self.language,
        }
        if self.description:
            data["description"] = self.description
        if self.author:
            data["author"] = self.author
        if self.license:
            data["license"] = self.license
        if self.vendor:
            data["vendor"] = self.vendor
        if self.top:
            data["top"] = self.top
        if self.packages:
            data["packages"] = [pkg.to_dict() for pkg in self.packages]
        if self.includes:
            data["includes"] = self.includes
        if self.defines:
            data["defines"] = self.defines

        # IMPORTANT: modules as list of dicts
        data["modules"] = [m.to_dict() for m in self.modules]

        return data

    def get_rtl_files(self, files: Optional[List[Path]] = None) -> List[Path]:
        """Get all RTL files in compilation order.

        If `files` is provided, append into it (avoiding duplicates).
        Otherwise, create and return a new list.

        Compilation order:
        1. Shared packages (must come first)
        2. Module files (in the order of `self.modules`)
        """
        if files is None:
            files = []
        seen = set(files)

        # 1. Packages first
        for pkg in self.packages:
            p = self.resolve_path(pkg.path)
            if p.exists() and p not in seen:
                files.append(p)
                seen.add(p)

        # 2. Module files (reuse the utility)
        return self.get_rtl_files_for_modules(self.modules, files)

    def get_rtl_files_for_modules(
        self, modules: Iterable[RTLModule], files: Optional[List[Path]] = None
    ) -> List[Path]:
        """Get RTL files for the given modules.

        If `files` is provided, append into it (avoiding duplicates).
        Otherwise, create and return a new list.
        """
        if files is None:
            files = []
        seen = set(files)

        for module in modules:
            for f in module.resolve_files():
                if f not in seen:
                    files.append(f)
                    seen.add(f)

        return files

    def get_include_dirs(self, includes: Optional[List[Path]] = None) -> List[Path]:
        """Get include directories.

        If `includes` is provided, append into it (avoiding duplicates).
        Otherwise, create and return a new list.
        """
        if includes is None:
            includes = []

        seen = set(includes)

        for inc in self.includes:
            p = self.resolve_path(inc)
            if p.exists() and p.is_dir() and p not in seen:
                includes.append(p)
                seen.add(p)

        return includes

    def get_modules(self, modules: Optional[List[RTLModule]] = None) -> List[RTLModule]:
        """Get all modules in this manifest.

        If `modules` is provided, append into it (avoiding duplicates by name).
        Otherwise, create and return a new list.
        """
        if modules is None:
            modules = []

        seen_names = {m.name for m in modules}

        for module in self.modules:
            if module.name not in seen_names:
                modules.append(module)
                seen_names.add(module.name)

        return modules

    def get_defines(self, defines: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get all defines.

        If `defines` is provided, update it (overriding existing keys).
        Otherwise, create and return a new dict.
        """
        if defines is None:
            defines = {}

        defines.update(self.defines)
        return defines

    def get_module_names(self, names: Optional[List[str]] = None) -> List[str]:
        """Get all module names.

        If `names` is provided, append into it (avoiding duplicates).
        Otherwise, create and return a new list.
        """
        if names is None:
            names = []

        seen = set(names)

        for module in self.modules:
            if module.name not in seen:
                names.append(module.name)
                seen.add(module.name)

        return names

    def get_pkg_files(self, files: Optional[List[Path]] = None) -> List[Path]:
        """Get package files that apply to all modules (modules == []).

        If `files` is provided, append into it (avoiding duplicates).
        Otherwise, create and return a new list.
        """
        if files is None:
            files = []
        seen = set(files)

        for pkg in self.packages:
            if pkg.modules:
                continue  # not global
            p = self.resolve_path(pkg.path)
            if p.exists() and p not in seen:
                files.append(p)
                seen.add(p)

        return files

    def get_pkg_files_for_module(
        self,
        module_name: str,
        files: Optional[List[Path]] = None,
    ) -> List[Path]:
        """Get all package files that apply to a specific module.

        Includes:
        - global packages (modules == [])
        - packages whose `modules` list contains `module_name`
        """
        if files is None:
            files = []
        seen = set(files)

        for pkg in self.packages:
            if pkg.modules and module_name not in pkg.modules:
                continue
            p = self.resolve_path(pkg.path)
            if p.exists() and p not in seen:
                files.append(p)
                seen.add(p)

        return files

    def get_pkg_file_by_name(self, name: str) -> Optional[Path]:
        """Get the resolved file path for a package by its name.

        Args:
            name: The package name to look up.

        Returns:
            Resolved Path if found and exists, None otherwise.
        """
        pkg = self.get_package(name)
        if not pkg:
            return None
        p = self.resolve_path(pkg.path)
        return p if p.exists() else None

    def get_pkg_files_by_names(
        self,
        names: List[str],
        files: Optional[List[Path]] = None,
    ) -> List[Path]:
        """Get package files by their names (for dependency resolution).

        Args:
            names: List of package names to include.
            files: Optional list to append to (avoids duplicates).

        Returns:
            List of resolved paths for the named packages.
        """
        if files is None:
            files = []
        seen = set(files)

        for name in names:
            pkg = self.get_package(name)
            if not pkg:
                continue
            p = self.resolve_path(pkg.path)
            if p.exists() and p not in seen:
                files.append(p)
                seen.add(p)

        return files

    def get_files_for_module(self, module_name: str) -> List[Path]:
        """Get compilation files for a specific module.

        Order:
        1. Packages (global + scoped to this module)
        2. That module's own RTL files
        """
        module = self.get_module(module_name)
        if not module:
            return []

        files: List[Path] = []
        self.get_pkg_files_for_module(module_name, files)
        self.get_rtl_files_for_modules([module], files)
        return files
