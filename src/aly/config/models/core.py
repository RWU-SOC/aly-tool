# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Core configuration classes for project-level settings."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any

from aly.config.models.helpers import HDLLanguage

# Constants
MANIFEST_FILENAME = "manifest.yaml"


@dataclass
class ProjectInfo:
    """Project metadata and identification."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = "Apache-2.0"
    repository: str = ""
    language: str = "systemverilog"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectInfo":
        """Create ProjectInfo from dictionary."""
        language = data.get("language", "systemverilog")
        if not HDLLanguage.is_valid(language):
            language = "systemverilog"

        return cls(
            name=data.get("name", "unnamed"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            license=data.get("license", "Apache-2.0"),
            repository=data.get("repository", ""),
            language=language,
        )


@dataclass
class FeatureFlags:
    """Feature toggles for optional project capabilities."""

    firmware: bool = False
    ip: bool = False
    constraints: bool = True
    formal: bool = False
    coverage: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureFlags":
        """Create FeatureFlags from dictionary."""
        if not data:
            return cls()
        return cls(
            firmware=data.get("firmware", False),
            ip=data.get("ip", False),
            constraints=data.get("constraints", True),
            formal=data.get("formal", False),
            coverage=data.get("coverage", False),
        )

    def is_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        return getattr(self, feature, False)


@dataclass
class DefaultsConfig:
    """Default tool selections for the project."""

    simulator: str = "xsim"
    synthesizer: str = "vivado"
    linter: str = "verilator"
    toolchain: str = ""  # Default firmware toolchain

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DefaultsConfig":
        """Create DefaultsConfig from dictionary."""
        if not data:
            return cls()
        return cls(
            simulator=data.get("simulator", "xsim"),
            synthesizer=data.get("synthesizer", "vivado"),
            linter=data.get("linter", "verilator"),
            toolchain=data.get("toolchain", ""),
        )


@dataclass
class PathsConfig:
    """Project directory structure configuration.

    Defines where different component types are located.
    Single path per type - KISS principle (no multi-path discovery).
    """

    build: str = "build"
    rtl: str = "rtl"
    tb: str = "tb"
    ip: str = "ip"
    firmware: str = "fw"
    constraints: str = "constraints"
    docs: str = "docs"
    scripts: str = "scripts"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PathsConfig":
        """Create PathsConfig from dictionary."""
        if not data:
            return cls()
        return cls(
            build=data.get("build", "build"),
            rtl=data.get("rtl", "rtl"),
            tb=data.get("tb", "tb"),
            ip=data.get("ip", "ip"),
            firmware=data.get("firmware", "fw"),
            constraints=data.get("constraints", "constraints"),
            docs=data.get("docs", "docs"),
            scripts=data.get("scripts", "scripts"),
        )

    def get_component_path(self, component_type: str) -> str:
        """Get path for a component type.

        Args:
            component_type: "rtl", "tb", "ip", "firmware", etc.

        Returns:
            Path string for that component type
        """
        return getattr(self, component_type, component_type)

    def as_dict(self) -> Dict[str, str]:
        """Convert PathsConfig to dictionary for registry.

        Returns:
            Dict mapping component type to path
        """
        return {
            "build": self.build,
            "rtl": self.rtl,
            "tb": self.tb,
            "ip": self.ip,
            "firmware": self.firmware,
            "constraints": self.constraints,
            "docs": self.docs,
            "scripts": self.scripts,
        }
