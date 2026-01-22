# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Testbench and test suite manifest classes - self-contained."""

import glob as globlib
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from aly.config.models.helpers import HDLLanguage, ValidationLevel, ValidationMessage


# =============================================================================
# Testbench - Single testbench in a collection
# =============================================================================


@dataclass
class Testbench:
    """A single testbench within a collection.

    Self-contained class with no inheritance or helper dependencies.
    Uses plain dicts for nested structures.

    Example YAML:
    ```yaml
    testbenches:
      - name: tb_mux
        author: Mohamed Aly
        version: 1.0.0
        description: testbench for mux module
        language: systemverilog
        top: tb_mux
        files:
          - tb_mux/tb_mux.sv
          - tb_mux/mux.sv
        includes:
          - include
        default_timeout: 10000
        dependencies:
          - name: another_rtl_module
            type: rtl
          - name: instr01loadbyte
            type: firmware
          - name: common_pkg
            type: package
    ```
    """

    name: str
    author: str = ""
    version: str = "1.0.0"
    description: str = ""
    language: str = "systemverilog"

    # Top module info (defaults to testbench name)
    top: Optional[str] = None

    # Source files
    files: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    defines: Dict[str, str] = field(default_factory=dict)

    # Dependencies (plain dicts: {name, type, required})
    dependencies: List[Dict[str, Any]] = field(default_factory=list)

    # Runtime config
    default_timeout: Union[int, str] = 10000  # int or "forever"
    plusargs: Dict[str, str] = field(default_factory=dict)

    # Tags for filtering
    tags: List[str] = field(default_factory=list)

    # Internal tracking
    _manifest_path: Optional[Path] = field(default=None, repr=False)

    @property
    def root_dir(self) -> Optional[Path]:
        """Get the directory containing the manifest."""
        if self._manifest_path:
            return self._manifest_path.parent
        return None

    @property
    def top_module(self) -> str:
        """Get the top module name (defaults to testbench name)."""
        return self.top if self.top else self.name

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

    def get_rtl_files(self) -> List[Path]:
        """Get testbench source files (alias for resolve_files)."""
        return self.resolve_files()

    def get_include_dirs(self) -> List[Path]:
        """Get include directories."""
        includes = []
        if not self.root_dir:
            return includes

        for inc in self.includes:
            p = self.resolve_path(inc)
            if p.exists():
                includes.append(p)
        return includes

    def get_rtl_deps(self) -> List[Dict[str, Any]]:
        """Get RTL dependencies (where type='rtl')."""
        return [d for d in self.dependencies if d.get("type") == "rtl"]

    def get_firmware_deps(self) -> List[Dict[str, Any]]:
        """Get firmware dependencies (where type='firmware')."""
        return [d for d in self.dependencies if d.get("type") == "firmware"]

    def get_package_deps(self) -> List[Dict[str, Any]]:
        """Get package dependencies (where type='package')."""
        return [d for d in self.dependencies if d.get("type") == "package"]

    def get_package_dep_names(self) -> List[str]:
        """Get names of package dependencies."""
        return [name for d in self.get_package_deps() if (name := d.get("name"))]

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], manifest_path: Optional[Path] = None
    ) -> "Testbench":
        """Create Testbench from dictionary."""
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
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            language=data.get("language", "systemverilog"),
            top=data.get("top"),
            files=data.get("files", []),
            includes=data.get("includes", []),
            defines=data.get("defines", {}),
            dependencies=deps,
            default_timeout=data.get("default_timeout", 10000),
            plusargs=data.get("plusargs", {}),
            tags=data.get("tags", []),
            _manifest_path=manifest_path,
        )

    @classmethod
    def from_list(
        cls, data: List[Dict[str, Any]], manifest_path: Optional[Path] = None
    ) -> List["Testbench"]:
        """Create list of Testbenches from list of dictionaries."""
        return [cls.from_dict(item, manifest_path) for item in (data or [])]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        d: Dict[str, Any] = {"name": self.name}

        if self.author:
            d["author"] = self.author
        if self.version != "1.0.0":
            d["version"] = self.version
        if self.description:
            d["description"] = self.description
        if self.language != "systemverilog":
            d["language"] = self.language
        if self.top:
            d["top"] = self.top
        if self.files:
            d["files"] = self.files
        if self.includes:
            d["includes"] = self.includes
        if self.defines:
            d["defines"] = self.defines
        if self.dependencies:
            d["dependencies"] = self.dependencies
        if self.default_timeout != 10000:
            d["default_timeout"] = self.default_timeout
        if self.plusargs:
            d["plusargs"] = self.plusargs
        if self.tags:
            d["tags"] = self.tags

        return d


# =============================================================================
# TestSuite - Test suite grouping multiple testbenches
# =============================================================================


@dataclass
class TestSuite:
    """Test suite grouping multiple testbenches.

    Self-contained class for defining test suites within a testbench manifest.

    Example YAML:
    ```yaml
    testsuites:
      - name: alu_test_suite
        description: Test suite for ALU operations
        testbenches:
          - tb_alu
          - tb_mux
        parallel: 4
        timeout: 60
        stop_on_fail: true
    ```
    """

    name: str
    description: str = ""

    # List of testbench names in this suite
    testbenches: List[str] = field(default_factory=list)

    # Execution options
    parallel: int = 1
    timeout: int = 60
    stop_on_fail: bool = False

    # Internal tracking
    _manifest_path: Optional[Path] = field(default=None, repr=False)

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], manifest_path: Optional[Path] = None
    ) -> "TestSuite":
        """Create TestSuite from dictionary."""
        return cls(
            name=data.get("name", "unnamed_suite"),
            description=data.get("description", ""),
            testbenches=data.get("testbenches", []),
            parallel=data.get("parallel", 1),
            timeout=data.get("timeout", 60),
            stop_on_fail=data.get("stop_on_fail", False),
            _manifest_path=manifest_path,
        )

    @classmethod
    def from_list(
        cls, data: List[Dict[str, Any]], manifest_path: Optional[Path] = None
    ) -> List["TestSuite"]:
        """Create list of TestSuites from list of dictionaries."""
        return [cls.from_dict(item, manifest_path) for item in (data or [])]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        d: Dict[str, Any] = {
            "name": self.name,
            "testbenches": self.testbenches,
        }

        if self.description:
            d["description"] = self.description
        if self.parallel != 1:
            d["parallel"] = self.parallel
        if self.timeout != 60:
            d["timeout"] = self.timeout
        if self.stop_on_fail:
            d["stop_on_fail"] = self.stop_on_fail

        return d


# =============================================================================
# TestbenchManifest - Testbench manifest with multi-testbench support
# =============================================================================


@dataclass
class TestbenchManifest:
    """Testbench manifest - self-contained, supports multiple testbenches.

    Self-contained class for managing testbench manifests with 'testbenches:' list.
    Uses standard manifest.yaml format for ProjectConfig discovery.

    Example manifest (manifest.yaml):
    ```yaml
    name: alu_tb
    type: testbench
    version: 1.0.0
    description: testbench configuration for my ALU RTL design
    author: Mohamed Aly

    testbenches:
      - name: tb_mux
        files:
          - tb_mux/tb_mux.sv
        dependencies:
          - name: mux_rtl
            type: rtl

      - name: tb_alu
        files:
          - tb_alu/tb_alu.sv
        dependencies:
          - name: alu_rtl
            type: rtl

    testsuites:
      - name: alu_test_suite
        description: Test suite for ALU operations
        testbenches:
          - tb_alu
          - tb_mux
    ```
    """

    # Manifest metadata
    name: str = "testbench"
    type: str = "testbench"
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = ""

    # Testbenches in this manifest
    testbenches: List[Testbench] = field(default_factory=list)

    # Test suites
    testsuites: List[TestSuite] = field(default_factory=list)

    # Internal tracking
    _manifest_path: Optional[Path] = field(default=None, repr=False)

    @property
    def root_dir(self) -> Optional[Path]:
        """Get the directory containing the manifest."""
        if self._manifest_path:
            return self._manifest_path.parent
        return None

    def get_testbench(self, name: str) -> Optional[Testbench]:
        """Get a testbench by name."""
        for tb in self.testbenches:
            if tb.name == name:
                return tb
        return None

    def get_testsuite(self, name: str) -> Optional[TestSuite]:
        """Get a test suite by name."""
        for suite in self.testsuites:
            if suite.name == name:
                return suite
        return None

    def add_testbench(self, testbench: Testbench) -> bool:
        """Add a testbench to the manifest.

        Returns:
            True if added, False if name already exists.
        """
        if self.get_testbench(testbench.name):
            return False
        self.testbenches.append(testbench)
        return True

    def add_testsuite(self, suite: TestSuite) -> bool:
        """Add a test suite to the manifest.

        Returns:
            True if added, False if name already exists.
        """
        if self.get_testsuite(suite.name):
            return False
        self.testsuites.append(suite)
        return True

    def get_testbench_names(self) -> List[str]:
        """Get list of testbench names."""
        return [tb.name for tb in self.testbenches]

    def get_testsuite_names(self) -> List[str]:
        """Get list of test suite names."""
        return [s.name for s in self.testsuites]

    def validate(self) -> List[ValidationMessage]:
        """Validate testbench manifest configuration."""
        messages: List[ValidationMessage] = []

        # Validate type
        if self.type != "testbench":
            messages.append(
                ValidationMessage(
                    level=ValidationLevel.WARNING,
                    message=f"Type should be 'testbench', got '{self.type}'",
                    file=self._manifest_path,
                    field="type",
                )
            )

        # Warning if no testbenches
        if not self.testbenches:
            messages.append(
                ValidationMessage(
                    level=ValidationLevel.WARNING,
                    message="Testbench manifest has no testbenches defined",
                    file=self._manifest_path,
                    field="testbenches",
                )
            )

        # Validate each testbench
        for tb in self.testbenches:
            # Must have files
            if not tb.files:
                messages.append(
                    ValidationMessage(
                        level=ValidationLevel.ERROR,
                        message=f"Testbench '{tb.name}' requires at least one file",
                        file=self._manifest_path,
                        field=f"testbenches[{tb.name}].files",
                    )
                )

            # Validate language
            if not HDLLanguage.is_valid(tb.language):
                messages.append(
                    ValidationMessage(
                        level=ValidationLevel.ERROR,
                        message=f"Testbench '{tb.name}' has invalid language: {tb.language}",
                        file=self._manifest_path,
                        field=f"testbenches[{tb.name}].language",
                    )
                )

        # Validate test suites reference existing testbenches
        tb_names = set(self.get_testbench_names())
        for suite in self.testsuites:
            for tb_name in suite.testbenches:
                if tb_name not in tb_names:
                    messages.append(
                        ValidationMessage(
                            level=ValidationLevel.WARNING,
                            message=f"Test suite '{suite.name}' references unknown testbench: {tb_name}",
                            file=self._manifest_path,
                            field=f"testsuites[{suite.name}].testbenches",
                        )
                    )

        return messages

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], manifest_path: Optional[Path] = None
    ) -> "TestbenchManifest":
        """Create TestbenchManifest from dictionary."""
        return cls(
            name=data.get("name", "testbench"),
            type=data.get("type", "testbench"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            license=data.get("license", ""),
            testbenches=Testbench.from_list(data.get("testbenches", []), manifest_path),
            testsuites=TestSuite.from_list(data.get("testsuites", []), manifest_path),
            _manifest_path=manifest_path,
        )

    @classmethod
    def load(cls, path: Path) -> "TestbenchManifest":
        """Load TestbenchManifest from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls.from_dict(data, path)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        d: Dict[str, Any] = {
            "name": self.name,
            "type": self.type,
        }

        if self.version != "1.0.0":
            d["version"] = self.version
        if self.description:
            d["description"] = self.description
        if self.author:
            d["author"] = self.author
        if self.license:
            d["license"] = self.license

        if self.testbenches:
            d["testbenches"] = [tb.to_dict() for tb in self.testbenches]
        if self.testsuites:
            d["testsuites"] = [s.to_dict() for s in self.testsuites]

        return d

    def save(self, path: Optional[Path] = None) -> None:
        """Save manifest to YAML file."""
        save_path = path or self._manifest_path
        if not save_path:
            raise ValueError("No path specified and no manifest path set")

        with open(save_path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
