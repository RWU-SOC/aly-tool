# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Unified configuration and component registry for ALY projects.

This module provides the main ProjectConfig class that loads and manages
all configuration from the .aly/ directory and discovers project components
through manifest.yaml files.

Configuration structure:
- config.yaml: Project info, features, defaults, paths
- toolchains.yaml: Firmware toolchain definitions
- sim.yaml: Simulation tool settings
- synth.yaml: Synthesis settings
- lint.yaml: Lint settings
- constraints.yaml: Design constraints
- fpga.yaml: FPGA programming settings

Components (RTL, testbenches, firmware, IP) are discovered via manifest.yaml
files in their respective directories.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Type, NoReturn
from dataclasses import dataclass, field

from aly.config.models import (
    ProjectInfo,
    FeatureFlags,
    DefaultsConfig,
    PathsConfig,
    SimConfig,
    SynthConfig,
    LintConfig,
    ConstraintsConfig,
    FPGAConfig,
    SimToolConfig,
    Toolchain,
    RTLManifest,
    RTLModule,
    TestbenchManifest,
    Testbench,
    TestSuite,
    FirmwareManifest,
    FirmwareBuild,
    IPManifest,
)
from aly.config.models.helpers import RTLPackage
from aly.log import dbg, wrn, err, die

# Manifest filename constant
MANIFEST_FILENAME = "manifest.yaml"

@dataclass
class UnitRef:
    kind: str              # "rtl_module", "testbench", "firmware_build", ...
    name: str              # module/testbench/build name
    manifest_type: str     # "rtl", "testbench", "firmware", ...
    manifest_name: str     # parent manifest name
    manifest: Any          # parent manifest object
    obj: Any               # the module/testbench/build object

class ProjectConfig:
    """
    Unified configuration manager and component registry for ALY projects.

    Loads configuration from .aly/ directory and discovers components through
    manifest.yaml files in configured paths. Provides unified access to all
    project settings and components.

    Example:
        config = ProjectConfig.load(".")

        # Access project info
        print(config.info.name)

        # Get RTL block
        cpu = config.get_rtl_block("cpu")

        # Get testbench
        tb = config.get_testbench("tb_alu")

        # List all components
        rtl_blocks = config.list_rtl_blocks()
        
        # Resolve dependencies
        deps = config.resolve_rtl_deps(tb)
    """

    CONFIG_DIR = ".aly"

    # Config file list
    CONFIG_FILES = {
        "config": "config.yaml",
        "toolchains": "toolchains.yaml",
        "sim": "sim.yaml",
        "synth": "synth.yaml",
        "lint": "lint.yaml",
        "constraints": "constraints.yaml",
        "fpga": "fpga.yaml",
    }

    def __init__(self, project_root: Path):
        """Initialize configuration manager."""
        self.project_root = project_root
        self.config_dir = project_root / self.CONFIG_DIR

        # Core configuration (always loaded)
        self.info: Optional[ProjectInfo] = None
        self.features: Optional[FeatureFlags] = None
        self.defaults: Optional[DefaultsConfig] = None
        self.paths: Optional[PathsConfig] = None

        # Tool configurations (lazy loaded)
        self._sim: Optional[SimConfig] = None
        self._synth: Optional[SynthConfig] = None
        self._lint: Optional[LintConfig] = None
        self._constraints: Optional[ConstraintsConfig] = None
        self._fpga: Optional[FPGAConfig] = None

        # Component registry (lazy loaded)
        self._components: Dict[str, Dict[str, Any]] = {}
        self._toolchains: Dict[str, Toolchain] = {}
        self._discovered: bool = False

        # Raw data cache
        self._raw: Dict[str, Any] = {}

        # New: registry of units
        self._units: Dict[str, Dict[str, UnitRef]] = {
            "rtl_module": {},
            "testbench": {},
            "firmware_build": {},
            "package": {},
        }

        # Initialize component type buckets
        for component_type in ["rtl", "ip", "testbench", "firmware"]:
            self._components[component_type] = {}

    # =========================================================================
    # Loading and Initialization
    # =========================================================================

    @classmethod
    def load(cls, project_root: Path | str) -> "ProjectConfig":
        """
        Load configuration from project root.

        Args:
            project_root: Path to project root directory

        Returns:
            Loaded ProjectConfig instance

        Raises:
            SystemExit: If configuration is missing or invalid
        """
        if isinstance(project_root, str):
            project_root = Path(project_root)

        config = cls(project_root)

        if not config.config_dir.exists():
            die(
                f"Configuration directory not found: {config.config_dir}\n"
                f"Run 'aly init' to initialize a project."
            )

        main_config = config.config_dir / "config.yaml"
        if not main_config.exists():
            die(f"Main configuration file not found: {main_config}")

        config._load_main_config()
        config._load_tool_configs()
        config._load_toolchains()

        return config

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file safely."""
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except yaml.YAMLError as e:
            die(f"Invalid YAML in {path}: {e}")

    def _load_main_config(self):
        """Load main config.yaml file."""
        config_path = self.config_dir / "config.yaml"
        data = self._load_yaml(config_path)
        self._raw["config"] = data

        self.info = ProjectInfo.from_dict(data.get("project", {}))
        self.features = FeatureFlags.from_dict(data.get("features", {}))
        self.defaults = DefaultsConfig.from_dict(data.get("defaults", {}))
        self.paths = PathsConfig.from_dict(data.get("paths", {}))

    def _load_tool_configs(self):
        """Load tool configuration files."""
        tool_map = {
            "sim": ("_sim", SimConfig),
            "synth": ("_synth", SynthConfig),
            "lint": ("_lint", LintConfig),
            "constraints": ("_constraints", ConstraintsConfig),
            "fpga": ("_fpga", FPGAConfig),
        }

        for name, (attr, config_cls) in tool_map.items():
            filename = self.CONFIG_FILES.get(name)
            if filename:
                file_path = self.config_dir / filename
                if file_path.exists():
                    data = self._load_yaml(file_path)
                    self._raw[name] = data
                    setattr(self, attr, config_cls.from_dict(data, self.project_root))

    def _load_toolchains(self) -> None:
        """Load toolchain configurations from .aly/toolchains.yaml."""
        toolchains_path = self.config_dir / "toolchains.yaml"
        if not toolchains_path.exists():
            dbg("No toolchains.yaml found")
            return

        try:
            data = self._load_yaml(toolchains_path)
            toolchains_data = data.get("toolchains", {})

            for name, tc_data in toolchains_data.items():
                if isinstance(tc_data, dict):
                    try:
                        self._toolchains[name] = Toolchain.from_dict(name, tc_data)
                    except Exception as e:
                        wrn(f"Failed to parse toolchain {name}: {e}")
        except Exception as e:
            wrn(f"Failed to load toolchains.yaml: {e}")

    # =========================================================================
    # Component Discovery
    # =========================================================================

    def discover_all(self) -> None:
        """Scan all configured paths for manifest.yaml files.

        This is the main discovery method that populates the component registry.
        It's called lazily on first access to any get/list method.
        """
        if self._discovered:
            return

        dbg(f"Starting component discovery in {self.project_root}")

        # Map path types to expected manifest types
        path_type_mapping = {
            "rtl": ["rtl"],
            "tb": ["testbench"],
            "ip": ["ip"],
            "firmware": ["firmware"],
        }

        for path_type, expected_types in path_type_mapping.items():
            paths = self.paths.as_dict().get(path_type, []) if self.paths else []
            if isinstance(paths, str):
                paths = [paths]

            for path in paths:
                self._scan_directory(path, expected_types)

        self._discovered = True
        dbg(
            f"Discovery complete: {sum(len(v) for v in self._components.values())} components"
        )

    def _scan_directory(
        self, path: str, expected_types: Optional[List[str]] = None
    ) -> None:
        """Recursively scan a directory for manifest.yaml files.

        Args:
            path: Relative path from project root to scan
            expected_types: Optional list of expected manifest types
        """
        root = self.project_root / path
        if not root.exists():
            dbg(f"Path does not exist: {root}")
            return

        
        # Find all manifest.yaml files recursively
        for manifest_path in root.rglob(MANIFEST_FILENAME):
            try:
                manifest = self._load_manifest(manifest_path)
                if manifest:
                    self._register(manifest)

                    # For IPs, also scan nested directories
                    manifest_type = getattr(manifest, "type", None)
                    if manifest_type == "ip":
                        self._scan_ip_subdirs(manifest_path.parent)
            except Exception as e:
                wrn(f"Failed to load manifest {manifest_path}: {e}")

    def _scan_ip_subdirs(self, ip_root: Path) -> None:
        """Scan IP subdirectories for nested manifests.

        Args:
            ip_root: Path to the IP directory (parent of manifest.yaml)
        """
        subdirs = ["rtl", "tb", "fw", "firmware"]

        for subdir in subdirs:
            subdir_path = ip_root / subdir
            if subdir_path.exists():
                for manifest_path in subdir_path.rglob(MANIFEST_FILENAME):
                    try:
                        manifest = self._load_manifest(manifest_path)
                        if manifest:
                            self._register(manifest)
                    except Exception as e:
                        wrn(f"Failed to load IP sub-manifest {manifest_path}: {e}")

    def _load_manifest(self, path: Path) -> Optional[Any]:
        """Load and parse a manifest.yaml file.

        Args:
            path: Path to the manifest.yaml file

        Returns:
            Typed manifest object or None if type is unknown
        """
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            wrn(f"Failed to parse YAML in {path}: {e}")
            return None

        manifest_type = data.get("type")
        if not manifest_type:
            dbg(f"Manifest has no type field: {path}")
            return None

        loaders: Dict[str, Type] = {
            "rtl": RTLManifest,
            "ip": IPManifest,
            "testbench": TestbenchManifest,
            "firmware": FirmwareManifest,
        }

        loader_class = loaders.get(manifest_type)
        if loader_class is None:
            dbg(f"Unknown manifest type '{manifest_type}' in {path}")
            return None

        try:
            if manifest_type == "rtl":
                return loader_class.load(path)
            else:
                return loader_class.from_dict(data, path)
        except Exception as e:
            wrn(f"Failed to create {manifest_type} manifest from {path}: {e}")
            return None

    def _register(self, manifest: Any) -> None:
        """Register a manifest in the appropriate type bucket.

        Args:
            manifest: Manifest object with `type` and `name` attributes
        """
        manifest_type = getattr(manifest, "type", None)
        manifest_name = getattr(manifest, "name", None)

        if not manifest_type or not manifest_name:
            wrn(f"Cannot register manifest without type or name: {manifest}")
            return

        if manifest_name in self._components.get(manifest_type, {}):
            dbg(
                f"Duplicate {manifest_type} manifest: {manifest_name} (keeping first)"
            )
            return

        self._components[manifest_type][manifest_name] = manifest
        dbg(f"Registered {manifest_type}: {manifest_name}")
        
        
        # --- Register units inside the manifest -------------------------------

        # 1) RTL modules
        if manifest_type == "rtl" and hasattr(manifest, "modules"):
            for module in manifest.modules:
                key = module.name  # or f"{manifest_name}:{module.name}" if you want namespaced
                if key in self._units["rtl_module"]:
                    wrn(
                        f"Duplicate RTL module name '{key}' "
                        f"(from manifest {manifest_name})"
                    )
                    continue
                self._units["rtl_module"][key] = UnitRef(
                    kind="rtl_module",
                    name=module.name,
                    manifest_type="rtl",
                    manifest_name=manifest_name,
                    manifest=manifest,
                    obj=module,
                )

        # 2) Testbenches (once TestbenchManifest has a .testbenches list)
        if manifest_type == "testbench" and hasattr(manifest, "testbenches"):
            for tb in manifest.testbenches:
                key = tb.name
                if key in self._units["testbench"]:
                    wrn(
                        f"Duplicate testbench name '{key}' "
                        f"(from manifest {manifest_name})"
                    )
                    continue
                self._units["testbench"][key] = UnitRef(
                    kind="testbench",
                    name=tb.name,
                    manifest_type="testbench",
                    manifest_name=manifest_name,
                    manifest=manifest,
                    obj=tb,
                )

        # 3) Firmware builds (once FirmwareManifest has a .builds or similar)
        if manifest_type == "firmware" and hasattr(manifest, "builds"):
            for build in manifest.builds:
                key = build.name  # or build.id / build.target, depending on your schema
                if key in self._units["firmware_build"]:
                    wrn(
                        f"Duplicate firmware build name '{key}' "
                        f"(from manifest {manifest_name})"
                    )
                    continue
                self._units["firmware_build"][key] = UnitRef(
                    kind="firmware_build",
                    name=key,
                    manifest_type="firmware",
                    manifest_name=manifest_name,
                    manifest=manifest,
                    obj=build,
                )

        # 4) Named packages (from RTL manifests)
        if manifest_type == "rtl" and hasattr(manifest, "packages"):
            for pkg in manifest.packages:
                if not pkg.name:
                    continue  # skip unnamed packages
                key = pkg.name
                if key in self._units["package"]:
                    wrn(
                        f"Duplicate package name '{key}' "
                        f"(from manifest {manifest_name})"
                    )
                    continue
                self._units["package"][key] = UnitRef(
                    kind="package",
                    name=pkg.name,
                    manifest_type="rtl",
                    manifest_name=manifest_name,
                    manifest=manifest,
                    obj=pkg,
                )


    # =========================================================================
    # Manifest Access (low-level, manifest-centric)
    # =========================================================================

    def _ensure_discovered(self) -> None:
        """Ensure manifests and units have been discovered."""
        if not self._discovered:
            self.discover_all()

    def get(self, manifest_type: str, name: str) -> Optional[Any]:
        """Get a manifest by type and name.

        Args:
            manifest_type: Component type (rtl, ip, testbench, firmware, test_suite)
            name: Manifest name

        Returns:
            Manifest object or None if not found.
        """
        self._ensure_discovered()
        return self._components.get(manifest_type, {}).get(name)

    def list(self, manifest_type: str) -> List[str]:
        """List all manifest names of a specific type.

        Args:
            manifest_type: Component type

        Returns:
            List of manifest names.
        """
        self._ensure_discovered()
        return list(self._components.get(manifest_type, {}).keys())

    def get_all(self, manifest_type: str) -> Dict[str, Any]:
        """Get all manifests of a specific type.

        Args:
            manifest_type: Component type

        Returns:
            Dict mapping name to manifest object.
        """
        self._ensure_discovered()
        return self._components.get(manifest_type, {}).copy()
    

    # =========================================================================
    # Convenience Methods for Components (unit-centric)
    # =========================================================================

    # ------------------------- Generic unit access ---------------------------

    def get_unit(self, kind: str, name: str) -> Optional[UnitRef]:
        """Get a unit (rtl_module, testbench, firmware_build, ...) by kind and name."""
        self._ensure_discovered()
        return self._units.get(kind, {}).get(name)

    def list_units(self, kind: str) -> List[str]:
        """List all unit names of a given kind."""
        self._ensure_discovered()
        return list(self._units.get(kind, {}).keys())

    # ------------------------- RTL module units -----------------------------

    def get_rtl_module(self, name: str) -> Optional[UnitRef]:
        """Get a single RTL module unit by name."""
        return self.get_unit("rtl_module", name)

    def list_rtl_modules(self) -> List[str]:
        """List all RTL module unit names."""
        return self.list_units("rtl_module")
    
    def iter_rtl_modules(self):
        """Iterate over all RTL module units.

        Yields:
            UnitRef objects for each RTL module.
        """
        self._ensure_discovered()
        return self._units["rtl_module"].values()
    
    def get_rtl_module_objects(self) -> Dict[str, tuple[RTLModule, RTLManifest]]:
        """Get all RTL modules with their parent manifests.

        Returns:
            Dict: module_name -> (module_obj, parent_manifest)
        """
        self._ensure_discovered()
        result: Dict[str, tuple[RTLModule, RTLManifest]] = {}
        for name, ref in self._units["rtl_module"].items():
            result[name] = (ref.obj, ref.manifest)  # obj is RTLModule, manifest is RTLManifest
        return result
    
    
    def get_rtl_module_files(self, module_name: str) -> List[Path]:
        """Get compilation files (packages + module files) for a given RTL module.

        Module is looked up project-wide, by name.
        """
        ref = self.get_rtl_module(module_name)
        if not ref:
            return []
        module: RTLModule = ref.obj
        manifest: RTLManifest = ref.manifest
        return manifest.get_files_for_module(module.name)


    def get_rtl_module_package_files(self, module_name: str) -> List[Path]:
        """Get package files that apply to a given RTL module."""
        ref = self.get_rtl_module(module_name)
        if not ref:
            return []
        module: RTLModule = ref.obj
        manifest: RTLManifest = ref.manifest
        return manifest.get_pkg_files_for_module(module.name)

    # ------------------------- Testbench units ------------------------------

    def get_testbench_unit(self, name: str) -> Optional[UnitRef]:
        """Get a single testbench unit by name.

        Requires that TestbenchManifest exposes a `testbenches` list and that
        `_register()` populates `_units["testbench"]`.
        """
        return self.get_unit("testbench", name)

    def list_testbench_units(self) -> List[str]:
        """List all testbench unit names."""
        return self.list_units("testbench")

    def get_testbench(self, name: str) -> Optional[Any]:
        """Get a testbench by name (returns Testbench object).

        This is a convenience method that returns the testbench object directly,
        rather than the UnitRef wrapper.
        """
        ref = self.get_testbench_unit(name)
        return ref.obj if ref else None

    def list_testbenches(self) -> List[str]:
        """List all testbench names.

        Convenience alias for list_testbench_units().
        """
        return self.list_testbench_units()

    def iter_testbenches(self):
        """Iterate over all testbench units.

        Yields:
            UnitRef objects for each testbench.
        """
        self._ensure_discovered()
        return self._units["testbench"].values()

    # ------------------------- Test suite access -----------------------------

    def get_testsuite(self, name: str) -> Optional[Any]:
        """Get a test suite by name (searches all testbench manifests).

        Returns:
            TestSuite object or None if not found.
        """
        self._ensure_discovered()
        for manifest in self._components.get("testbench", {}).values():
            if hasattr(manifest, "testsuites"):
                for suite in manifest.testsuites:
                    if suite.name == name:
                        return suite
        return None

    def list_testsuites(self) -> List[str]:
        """List all test suite names."""
        self._ensure_discovered()
        names = []
        for manifest in self._components.get("testbench", {}).values():
            if hasattr(manifest, "testsuites"):
                names.extend(s.name for s in manifest.testsuites)
        return names

    # ------------------------- Dependency Resolution -------------------------

    def resolve_rtl_deps(self, unit: Any, _visited: Optional[set] = None) -> List[UnitRef]:
        """Recursively resolve RTL dependencies for a unit (testbench or RTL module).

        Args:
            unit: Testbench or RTLModule object with dependencies list
            _visited: Internal set to track visited modules and prevent cycles

        Returns:
            List of UnitRef objects (containing both RTLModule obj and RTLManifest manifest)
            in dependency order (dependencies before dependents)
        """
        if _visited is None:
            _visited = set()

        resolved = []
        deps = getattr(unit, "dependencies", [])

        for dep in deps:
            if isinstance(dep, dict) and dep.get("type") == "rtl":
                dep_name = dep.get("name", "")
                if not dep_name:
                    continue

                # Skip if already visited (avoid cycles)
                if dep_name in _visited:
                    continue

                ref = self.get_rtl_module(dep_name)
                if ref:
                    _visited.add(dep_name)

                    # Recursively resolve dependencies of this RTL module
                    module: RTLModule = ref.obj
                    sub_deps = self.resolve_rtl_deps(module, _visited)

                    # Add sub-dependencies first (topological order)
                    for sub_ref in sub_deps:
                        if sub_ref not in resolved:
                            resolved.append(sub_ref)

                    # Then add this dependency
                    if ref not in resolved:
                        resolved.append(ref)

        return resolved

    def resolve_package_deps(self, testbench: Any) -> List[UnitRef]:
        """Resolve package dependencies for a testbench.

        Args:
            testbench: Testbench object with dependencies list

        Returns:
            List of UnitRef objects (containing RTLPackage obj and parent RTLManifest)
        """
        resolved = []
        deps = getattr(testbench, "dependencies", [])
        for dep in deps:
            if isinstance(dep, dict) and dep.get("type") == "package":
                ref = self.get_package_unit(dep.get("name", ""))
                if ref:
                    resolved.append(ref)
        return resolved

    def resolve_package_dep_files(self, testbench: Any) -> List[Path]:
        """Resolve package dependencies for a testbench and return file paths.

        Args:
            testbench: Testbench object with dependencies list

        Returns:
            List of resolved Paths for package files.
        """
        files: List[Path] = []
        seen: set[Path] = set()

        for ref in self.resolve_package_deps(testbench):
            pkg: RTLPackage = ref.obj
            manifest: RTLManifest = ref.manifest
            p = manifest.resolve_path(pkg.path)
            if p.exists() and p not in seen:
                files.append(p)
                seen.add(p)

        return files

    # ------------------------- Package units ----------------------------------

    def get_package_unit(self, name: str) -> Optional[UnitRef]:
        """Get a package unit by name.

        Args:
            name: The package name to look up.

        Returns:
            UnitRef containing the RTLPackage obj and parent RTLManifest.
        """
        return self.get_unit("package", name)

    def get_package(self, name: str) -> Optional[RTLPackage]:
        """Get a package by name (returns RTLPackage object).

        This is a convenience method that returns the package object directly,
        rather than the UnitRef wrapper.
        """
        ref = self.get_package_unit(name)
        return ref.obj if ref else None

    def list_packages(self) -> List[str]:
        """List all named package names."""
        return self.list_units("package")

    def iter_packages(self):
        """Iterate over all package units.

        Yields:
            UnitRef objects for each named package.
        """
        self._ensure_discovered()
        return self._units["package"].values()

    def get_package_file(self, name: str) -> Optional[Path]:
        """Get the resolved file path for a package by name.

        Args:
            name: The package name to look up.

        Returns:
            Resolved Path if found and exists, None otherwise.
        """
        ref = self.get_package_unit(name)
        if not ref:
            return None
        pkg: RTLPackage = ref.obj
        manifest: RTLManifest = ref.manifest
        p = manifest.resolve_path(pkg.path)
        return p if p.exists() else None

    def get_package_files_by_names(self, names: List[str]) -> List[Path]:
        """Get package files by their names (for dependency resolution).

        Args:
            names: List of package names to include.

        Returns:
            List of resolved paths for the named packages.
        """
        files: List[Path] = []
        seen: set[Path] = set()

        for name in names:
            p = self.get_package_file(name)
            if p and p not in seen:
                files.append(p)
                seen.add(p)

        return files

    # ------------------------- Firmware build units -------------------------

    def get_firmware_build(self, name: str) -> Optional[UnitRef]:
        """Get a single firmware build unit by name.

        Requires that FirmwareManifest exposes a `builds` list and that
        `_register()` populates `_units["firmware_build"]`.
        """
        return self.get_unit("firmware_build", name)

    def list_firmware_builds(self) -> List[str]:
        """List all firmware build unit names."""
        return self.list_units("firmware_build")

    def get_firmware(self, name: str) -> Optional[FirmwareBuild]:
        """Get a firmware build by name (returns FirmwareBuild object).

        This is a convenience method that returns the build object directly,
        rather than the UnitRef wrapper.
        """
        ref = self.get_firmware_build(name)
        return ref.obj if ref else None

    def list_firmware(self) -> List[str]:
        """List all firmware build names.

        Convenience alias for list_firmware_builds().
        """
        return self.list_firmware_builds()

    def iter_firmware_builds(self):
        """Iterate over all firmware build units.

        Yields:
            UnitRef objects for each firmware build.
        """
        self._ensure_discovered()
        return self._units["firmware_build"].values()

    # ------------------------- Toolchain access ------------------------------

    def get_toolchain(self, name: str) -> Optional[Toolchain]:
        """Get a toolchain by name."""
        return self._toolchains.get(name)

    def list_toolchains(self) -> List[str]:
        """List all loaded toolchain names."""
        return list(self._toolchains.keys())

    # ------------------------- IP manifests (no units) ----------------------

    def get_ip(self, name: str) -> Optional[IPManifest]:
        """Get an IP manifest by name."""
        return self.get("ip", name)

    def list_ips(self) -> List[str]:
        """List all discovered IP manifest names."""
        return self.list("ip")


    # =========================================================================
    # Configuration Access (Lazy-Loaded Properties)
    # =========================================================================

    @property
    def sim(self) -> SimConfig:
        """Simulation configuration."""
        if self._sim is None:
            self._sim = SimConfig(_project_root=self.project_root)
        return self._sim

    @property
    def synth(self) -> SynthConfig:
        """Synthesis configuration."""
        if self._synth is None:
            self._synth = SynthConfig(_project_root=self.project_root)
        return self._synth

    @property
    def lint(self) -> LintConfig:
        """Lint configuration."""
        if self._lint is None:
            self._lint = LintConfig(_project_root=self.project_root)
        return self._lint

    @property
    def constraints(self) -> ConstraintsConfig:
        """Constraints configuration."""
        if self._constraints is None:
            self._constraints = ConstraintsConfig(_project_root=self.project_root)
        return self._constraints

    @property
    def fpga(self) -> FPGAConfig:
        """FPGA configuration."""
        if self._fpga is None:
            self._fpga = FPGAConfig(_project_root=self.project_root)
        return self._fpga

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def is_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        if self.features:
            return self.features.is_enabled(feature)
        return False

    def resolve_path(self, path: str | Path) -> Path:
        """Resolve path relative to project root."""
        p = Path(path)
        if p.is_absolute():
            return p
        return (self.project_root / p).resolve()

    def get_sim_tool(self, name: Optional[str] = None) -> Optional[SimToolConfig]:
        """Get simulator tool configuration."""
        if name is None:
            name = self.defaults.simulator if self.defaults else "xsim"
        return self.sim.get_tool(name)

    def refresh(self) -> None:
        """Force re-discovery of all manifests."""
        self._discovered = False
        self._components = {
            t: {} for t in ["rtl", "ip", "testbench", "firmware"]
        }
        self._units = {
            "rtl_module": {},
            "testbench": {},
            "firmware_build": {},
            "package": {},
        }
        self._toolchains = {}
        self.discover_all()

    def summary(self) -> Dict[str, int]:
        """Get a summary of discovered components by type.

        Returns:
            Dict mapping component type to count
        """
        if not self._discovered:
            self.discover_all()

        return {t: len(v) for t, v in self._components.items()}

    def validate_all(self) -> Dict[str, List[Any]]:
        """Validate all discovered components.

        Returns:
            Dict mapping component type to list of validation messages
        """
        from aly.config.models import ValidationLevel

        results = {}

        for component_type in ["rtl", "ip", "testbench", "firmware"]:
            components = self.get_all(component_type)
            all_messages = []

            for name, manifest in components.items():
                messages = manifest.validate()
                errors = [m for m in messages if m.level == ValidationLevel.ERROR]
                if errors:
                    all_messages.extend(errors)

            if all_messages:
                results[component_type] = all_messages

        return results

    def __repr__(self) -> str:
        if not self.info:
            return f"ProjectConfig(not loaded, root={self.project_root})"
        
        if self._discovered:
            counts = ", ".join(
                f"{t}={len(v)}" for t, v in self._components.items() if v
            )
            return f"ProjectConfig({self.info.name} v{self.info.version}, {counts})"
        else:
            return f"ProjectConfig({self.info.name} v{self.info.version}, not discovered)"