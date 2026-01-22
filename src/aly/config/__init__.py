# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""ALY Configuration System - Registry-Based Architecture.

This package provides a modern, registry-based configuration system
for ALY projects. Components are discovered by scanning configured
directories for manifest.yaml files.

Configuration Structure:
    .aly/
    ├── aly.yaml          # Project metadata, features, defaults, paths
    ├── toolchains.yaml   # Toolchain definitions (riscv64, arm, etc.)
    ├── sim.yaml          # Simulation settings
    ├── synth.yaml        # Synthesis settings
    ├── lint.yaml         # Linting settings
    ├── constraints.yaml  # Design constraints
    └── fpga.yaml         # FPGA programming

Manifest Types (by `type:` field):
    rtl/<name>/manifest.yaml        # RTLManifest (type: rtl)
    tb/<name>/manifest.yaml         # TestbenchManifest (type: testbench)
    ip/<name>/manifest.yaml         # IPManifest (type: ip)
    fw/<name>/manifest.yaml         # FirmwareManifest (type: firmware)

Usage:
    from aly.config import ProjectConfig

    # Load project configuration
    config = ProjectConfig.load(project_root)

    # Access components
    rtl = config.get_rtl_module("cpu")
    tb = config.get_testbench("tb_cpu")
    fw = config.get_firmware("bootloader")

    # List components
    rtl_modules = config.list_rtl_modules()
    testbenches = config.list_testbenches()

    # Toolchain access
    tc = config.get_toolchain("riscv64")
"""

from aly.config.project_config import ProjectConfig

# Import all model types from the new modular structure
from aly.config.models import (
    # Base
    ValidationMessage,
    ValidationLevel,
    # Core
    ProjectInfo,
    FeatureFlags,
    DefaultsConfig,
    PathsConfig,
    HDLLanguage,
    MANIFEST_FILENAME,
    # Helpers
    RTLPackage,
    FirmwareFlags,
    MemFormat,
    # Manifests
    RTLManifest,
    IPManifest,
    RTLModule,
    TestbenchManifest,
    Testbench,
    TestSuite,
    FirmwareManifest,
    FirmwareBuild,
    # Firmware
    Toolchain,
    OutputSpec,
    # Tools
    SimToolConfig,
    SimConfig,
    SynthToolConfig,
    SynthTargetConfig,
    SynthConfig,
    LintToolConfig,
    LintRules,
    LintConfig,
    ConstraintSet,
    ClockConstraint,
    IODefaults,
    ConstraintsConfig,
    FPGAConfig,
)

__all__ = [
    # Loader
    "ProjectConfig",
    # Core
    "ProjectInfo",
    "FeatureFlags",
    "DefaultsConfig",
    "PathsConfig",
    "HDLLanguage",
    "MANIFEST_FILENAME",
    # Helpers
    "RTLPackage",
    "FirmwareFlags",
    "MemFormat",
    "ValidationMessage",
    "ValidationLevel",
    # Manifests
    "RTLManifest",
    "IPManifest",
    "RTLModule",
    "TestbenchManifest",
    "Testbench",
    "TestSuite",
    "FirmwareManifest",
    "FirmwareBuild",
    # Firmware
    "Toolchain",
    "OutputSpec",
    # Tools
    "SimToolConfig",
    "SimConfig",
    "SynthToolConfig",
    "SynthTargetConfig",
    "SynthConfig",
    "LintToolConfig",
    "LintRules",
    "LintConfig",
    "ConstraintSet",
    "ClockConstraint",
    "IODefaults",
    "ConstraintsConfig",
    "FPGAConfig",
]
