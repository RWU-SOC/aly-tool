# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Tests for new manifest types."""

import pytest
from pathlib import Path

from aly.config.models import (
    # Base classes
    RTLSection,
    TBSection,
    SimSection,
    SynthSection,
    # Manifest types
    ProjectManifest,
    LibraryManifest,
    IPManifest,
    FirmwareManifest,
    # Firmware
    OutputFormat,
    Toolchain,
    FirmwareManager,
    # Sources
    SourcesConfig,
    TestConfig,
)


class TestRTLSection:
    """Tests for RTLSection class."""

    def test_from_dict_empty(self):
        """Test creating RTLSection from empty dict."""
        section = RTLSection.from_dict({})
        assert section.files == []
        assert section.dirs == []
        assert section.packages == []
        assert section.includes == []
        assert section.defines == {}
        assert section.exclude == []

    def test_from_dict_full(self):
        """Test creating RTLSection from full dict."""
        data = {
            "packages": ["pkg/types_pkg.sv"],
            "files": ["core/cpu.sv", "core/alu.sv"],
            "dirs": ["periph"],
            "includes": ["include"],
            "defines": {"DEBUG": "1", "SYNTHESIS": ""},
            "exclude": ["**/*_tb.sv"],
        }
        section = RTLSection.from_dict(data)
        assert section.packages == ["pkg/types_pkg.sv"]
        assert section.files == ["core/cpu.sv", "core/alu.sv"]
        assert section.dirs == ["periph"]
        assert section.includes == ["include"]
        assert section.defines == {"DEBUG": "1", "SYNTHESIS": ""}
        assert section.exclude == ["**/*_tb.sv"]


class TestTBSection:
    """Tests for TBSection class."""

    def test_from_dict_empty(self):
        """Test creating TBSection from empty dict."""
        section = TBSection.from_dict({})
        assert section.files == []
        assert section.common_files == []

    def test_from_dict_full(self):
        """Test creating TBSection from full dict."""
        data = {
            "files": ["tb/tb_top.sv"],
            "dirs": ["tb/common"],
            "includes": ["tb/include"],
            "common_files": ["tb/clk_gen.sv"],
        }
        section = TBSection.from_dict(data)
        assert section.files == ["tb/tb_top.sv"]
        assert section.dirs == ["tb/common"]
        assert section.common_files == ["tb/clk_gen.sv"]


class TestSimSection:
    """Tests for SimSection class."""

    def test_from_dict_empty(self):
        """Test creating SimSection from empty dict."""
        section = SimSection.from_dict({})
        assert section.pre_compile == []
        assert section.post_sim == []

    def test_from_dict_full(self):
        """Test creating SimSection with scripts."""
        data = {
            "pre_compile": ["scripts/gen_params.py"],
            "post_sim": ["scripts/collect_coverage.sh"],
        }
        section = SimSection.from_dict(data)
        assert section.pre_compile == ["scripts/gen_params.py"]
        assert section.post_sim == ["scripts/collect_coverage.sh"]


class TestSynthSection:
    """Tests for SynthSection class."""

    def test_from_dict_empty(self):
        """Test creating SynthSection from empty dict."""
        section = SynthSection.from_dict({})
        assert section.constraints == []
        assert section.tcl_scripts == []

    def test_from_dict_full(self):
        """Test creating SynthSection with constraints."""
        data = {
            "constraints": ["timing.xdc", "pinout.xdc"],
            "tcl_scripts": ["setup.tcl"],
        }
        section = SynthSection.from_dict(data)
        assert section.constraints == ["timing.xdc", "pinout.xdc"]
        assert section.tcl_scripts == ["setup.tcl"]


class TestProjectManifest:
    """Tests for ProjectManifest class."""

    def test_from_dict_minimal(self):
        """Test creating ProjectManifest with minimal data."""
        data = {"name": "test_project"}
        manifest = ProjectManifest.from_dict(data)
        assert manifest.name == "test_project"
        assert manifest.version == "1.0.0"
        assert manifest.libs == []
        assert manifest.ips == []

    def test_from_dict_full(self):
        """Test creating ProjectManifest with full data."""
        data = {
            "name": "my_soc",
            "version": "2.0.0",
            "description": "My SoC Design",
            "rtl": {
                "packages": ["pkg/types_pkg.sv"],
                "files": ["core/cpu.sv"],
                "dirs": ["periph"],
            },
            "tb": {"files": ["tb/tb_soc.sv"]},
            "tests": {
                "smoke": {"top": "tb_soc", "timeout": 5000, "tags": ["smoke"]},
            },
            "libs": ["common_lib"],
            "ips": ["uart", "spi"],
        }
        manifest = ProjectManifest.from_dict(data)
        assert manifest.name == "my_soc"
        assert manifest.version == "2.0.0"
        assert manifest.rtl.packages == ["pkg/types_pkg.sv"]
        assert manifest.libs == ["common_lib"]
        assert manifest.ips == ["uart", "spi"]
        assert "smoke" in manifest.tests
        assert manifest.tests["smoke"].timeout == 5000

    def test_validate_missing_name(self):
        """Test validation catches missing name."""
        manifest = ProjectManifest.from_dict({"name": ""})
        errors = manifest.validate()
        assert len(errors) > 0
        assert "name" in errors[0].lower()


class TestLibraryManifest:
    """Tests for LibraryManifest class."""

    def test_from_dict_minimal(self):
        """Test creating LibraryManifest with minimal data."""
        data = {"name": "common_lib"}
        manifest = LibraryManifest.from_dict(data)
        assert manifest.name == "common_lib"
        assert manifest.parameters == {}
        assert manifest.libs == []

    def test_from_dict_with_parameters(self):
        """Test creating LibraryManifest with parameters."""
        data = {
            "name": "fifo_lib",
            "rtl": {"files": ["src/fifo.sv"]},
            "parameters": {
                "WIDTH": {"type": "int", "default": 8},
                "DEPTH": {"type": "int", "default": 16},
            },
            "libs": ["base_lib"],
        }
        manifest = LibraryManifest.from_dict(data)
        assert manifest.name == "fifo_lib"
        assert "WIDTH" in manifest.parameters
        assert manifest.parameters["WIDTH"]["default"] == 8
        assert manifest.libs == ["base_lib"]


class TestIPManifest:
    """Tests for IPManifest class."""

    def test_from_dict_minimal(self):
        """Test creating IPManifest with minimal data."""
        data = {"name": "uart"}
        manifest = IPManifest.from_dict(data)
        assert manifest.name == "uart"
        assert manifest.vendor == ""
        assert manifest.license == ""
        assert manifest.interfaces == []

    def test_from_dict_full(self):
        """Test creating IPManifest with full vendor metadata."""
        data = {
            "name": "axi_uart",
            "version": "2.1.0",
            "vendor": "acme_ip",
            "license": "Apache-2.0",
            "rtl": {"files": ["rtl/uart_tx.sv", "rtl/uart_rx.sv"]},
            "interfaces": ["axi4_lite", "uart"],
            "parameters": {"BAUD_RATE": {"type": "int", "default": 115200}},
        }
        manifest = IPManifest.from_dict(data)
        assert manifest.name == "axi_uart"
        assert manifest.vendor == "acme_ip"
        assert manifest.license == "Apache-2.0"
        assert "axi4_lite" in manifest.interfaces
        assert "uart" in manifest.interfaces
        assert "BAUD_RATE" in manifest.parameters


class TestOutputFormat:
    """Tests for OutputFormat class."""

    def test_from_dict_defaults(self):
        """Test OutputFormat default values."""
        fmt = OutputFormat.from_dict({})
        assert fmt.format == "mem"
        assert fmt.word_width == 32
        assert fmt.byte_order == "little"
        assert fmt.plusarg is None

    def test_from_dict_custom(self):
        """Test OutputFormat with custom values."""
        data = {
            "format": "hex",
            "word_width": 8,
            "byte_order": "big",
            "plusarg": "HEX_FILE",
        }
        fmt = OutputFormat.from_dict(data)
        assert fmt.format == "hex"
        assert fmt.word_width == 8
        assert fmt.byte_order == "big"
        assert fmt.plusarg == "HEX_FILE"


class TestToolchain:
    """Tests for Toolchain class."""

    def test_from_dict_minimal(self):
        """Test Toolchain with minimal data."""
        tc = Toolchain.from_dict("riscv32", {})
        assert tc.name == "riscv32"
        assert tc.prefix == "riscv32-"

    def test_from_dict_full(self):
        """Test Toolchain with full configuration."""
        data = {
            "prefix": "riscv32-unknown-elf-",
            "march": "rv32imc",
            "mabi": "ilp32",
            "cflags": ["-O2", "-g"],
            "ldflags": ["-nostdlib"],
        }
        tc = Toolchain.from_dict("riscv32", data)
        assert tc.prefix == "riscv32-unknown-elf-"
        assert tc.march == "rv32imc"
        assert tc.mabi == "ilp32"
        assert "-O2" in tc.cflags
        assert "-nostdlib" in tc.ldflags


class TestFirmwareManifest:
    """Tests for FirmwareManifest class."""

    def test_from_dict_minimal(self):
        """Test FirmwareManifest with minimal data."""
        data = {"name": "boot", "sources": ["main.c"]}
        manifest = FirmwareManifest.from_dict(data)
        assert manifest.name == "boot"
        assert manifest.sources == ["main.c"]
        assert len(manifest.outputs) == 1  # Default output

    def test_from_dict_full(self):
        """Test FirmwareManifest with full configuration."""
        data = {
            "name": "bootloader",
            "version": "1.0.0",
            "sources": ["src/boot.c", "src/startup.S"],
            "includes": ["include"],
            "linker_script": "linker/boot.ld",
            "start_addr": "0x00001000",
            "defines": {"DEBUG": "1"},
            "outputs": [
                {"format": "mem", "word_width": 32, "plusarg": "MEM_FILE"},
                {"format": "hex", "word_width": 8},
            ],
            "toolchain": "riscv32",
        }
        manifest = FirmwareManifest.from_dict(data)
        assert manifest.name == "bootloader"
        assert manifest.start_addr == 0x1000
        assert len(manifest.outputs) == 2
        assert manifest.outputs[0].plusarg == "MEM_FILE"
        assert manifest.toolchain == "riscv32"

    def test_validate_missing_sources(self):
        """Test validation catches missing sources."""
        manifest = FirmwareManifest.from_dict({"name": "test"})
        errors = manifest.validate()
        assert len(errors) > 0
        assert "source" in errors[0].lower()


class TestSourcesConfig:
    """Tests for SourcesConfig class."""

    def test_from_dict_defaults(self):
        """Test SourcesConfig with default values."""
        config = SourcesConfig.from_dict({}, Path("/tmp"))
        assert config.rtl_root == "rtl"
        assert config.lib_root == "lib"
        assert config.ip_root == "ip"
        assert config.top == "top"

    def test_from_dict_custom(self):
        """Test SourcesConfig with custom values."""
        data = {
            "top": "soc_top",
            "rtl_root": "src/rtl",
            "lib_root": "src/lib",
            "ip_root": "vendor/ip",
        }
        config = SourcesConfig.from_dict(data, Path("/tmp"))
        assert config.top == "soc_top"
        assert config.rtl_root == "src/rtl"
        assert config.lib_root == "src/lib"
        assert config.ip_root == "vendor/ip"


class TestFirmwareManager:
    """Tests for FirmwareManager class."""

    def test_from_dict_empty(self):
        """Test FirmwareManager with empty data."""
        manager = FirmwareManager.from_dict({}, Path("/tmp"))
        assert manager.default_toolchain == "none"
        assert manager.toolchains == {}

    def test_from_dict_with_toolchains(self):
        """Test FirmwareManager with toolchain configuration."""
        data = {
            "toolchain": "riscv32",
            "toolchains": {
                "riscv32": {
                    "prefix": "riscv32-unknown-elf-",
                    "march": "rv32imc",
                },
            },
        }
        manager = FirmwareManager.from_dict(data, Path("/tmp"))
        assert manager.default_toolchain == "riscv32"
        assert "riscv32" in manager.toolchains
        tc = manager.get_toolchain("riscv32")
        assert tc.march == "rv32imc"
