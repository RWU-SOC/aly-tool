# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""ALY Configuration Models - Modular Organization.

This module exports all configuration models in a clean, organized manner.
"""

from aly.config.models.core import (
    ProjectInfo,
    FeatureFlags,
    DefaultsConfig,
    PathsConfig,
    MANIFEST_FILENAME,
)
from aly.config.models.helpers import (
    HDLLanguage,
    RTLPackage,
    FirmwareFlags,
    MemFormat,
    ValidationMessage,
    ValidationLevel,
)
from aly.config.models.rtl import (
    RTLManifest,
    RTLModule,
)
from aly.config.models.ip import IPManifest
from aly.config.models.testbench import TestbenchManifest, Testbench, TestSuite
from aly.config.models.firmware import FirmwareManifest, FirmwareBuild, Toolchain, OutputSpec
from aly.config.models.tools import (
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
