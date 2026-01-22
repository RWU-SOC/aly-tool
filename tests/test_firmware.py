# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Tests for firmware backend."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

from aly.backends import FirmwareBackend, FirmwareResult
from aly.fw_gcc import GccFirmwareBackend
from aly.app.firmware import get_firmware_backend, build_firmware, FIRMWARE_BACKENDS


class TestFirmwareResult:
    """Tests for FirmwareResult dataclass."""

    def test_firmware_result_defaults(self):
        """Test FirmwareResult default values."""
        result = FirmwareResult(
            success=True,
            duration=1.5,
            build_name="test_build",
        )
        assert result.success is True
        assert result.duration == 1.5
        assert result.build_name == "test_build"
        assert result.elf_file is None
        assert result.bin_file is None
        assert result.mem_files == {}
        assert result.lst_file is None
        assert result.return_code == 0

    def test_firmware_result_with_files(self):
        """Test FirmwareResult with file paths."""
        result = FirmwareResult(
            success=True,
            duration=2.0,
            build_name="test_build",
            elf_file=Path("/build/test.elf"),
            bin_file=Path("/build/test.bin"),
            mem_files={"MEM_FILE": Path("/build/test.mem")},
        )
        assert result.elf_file == Path("/build/test.elf")
        assert result.bin_file == Path("/build/test.bin")
        assert "MEM_FILE" in result.mem_files

    def test_firmware_result_failure(self):
        """Test FirmwareResult for failed build."""
        result = FirmwareResult(
            success=False,
            duration=0.5,
            build_name="failed_build",
            stderr="Compilation error",
            return_code=1,
        )
        assert result.success is False
        assert result.stderr == "Compilation error"
        assert result.return_code == 1


class TestFirmwareBackendMemFileGeneration:
    """Tests for memory file generation."""

    def test_generate_mem_file_hex_format(self, tmp_path):
        """Test hex format memory file generation."""
        # Create a test binary
        bin_file = tmp_path / "test.bin"
        bin_file.write_bytes(b"\x13\x00\x00\x00\x93\x00\x00\x00")

        output_file = tmp_path / "test.hex"

        result = FirmwareBackend.generate_mem_file(
            bin_file, output_file, format="hex", word_width=32, byte_order="little"
        )

        assert result is True
        assert output_file.exists()
        content = output_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2
        assert lines[0] == "00000013"
        assert lines[1] == "00000093"

    def test_generate_mem_file_mem_format(self, tmp_path):
        """Test Verilog mem format generation."""
        bin_file = tmp_path / "test.bin"
        bin_file.write_bytes(b"\x13\x00\x00\x00")

        output_file = tmp_path / "test.mem"

        result = FirmwareBackend.generate_mem_file(
            bin_file, output_file, format="mem", word_width=32, byte_order="little"
        )

        assert result is True
        content = output_file.read_text()
        assert "Memory initialization file" in content
        assert "@0" in content
        assert "00000013" in content

    def test_generate_mem_file_coe_format(self, tmp_path):
        """Test Xilinx COE format generation."""
        bin_file = tmp_path / "test.bin"
        bin_file.write_bytes(b"\x13\x00\x00\x00\x93\x00\x00\x00")

        output_file = tmp_path / "test.coe"

        result = FirmwareBackend.generate_mem_file(
            bin_file, output_file, format="coe", word_width=32, byte_order="little"
        )

        assert result is True
        content = output_file.read_text()
        assert "memory_initialization_radix=16" in content
        assert "memory_initialization_vector" in content
        assert "00000013," in content
        assert "00000093;" in content

    def test_generate_mem_file_big_endian(self, tmp_path):
        """Test big endian byte order."""
        bin_file = tmp_path / "test.bin"
        bin_file.write_bytes(b"\x00\x00\x00\x13")

        output_file = tmp_path / "test.hex"

        result = FirmwareBackend.generate_mem_file(
            bin_file, output_file, format="hex", word_width=32, byte_order="big"
        )

        assert result is True
        content = output_file.read_text().strip()
        assert content == "00000013"

    def test_generate_mem_file_word_width_16(self, tmp_path):
        """Test 16-bit word width."""
        bin_file = tmp_path / "test.bin"
        bin_file.write_bytes(b"\x13\x00\x93\x00")

        output_file = tmp_path / "test.hex"

        result = FirmwareBackend.generate_mem_file(
            bin_file, output_file, format="hex", word_width=16, byte_order="little"
        )

        assert result is True
        content = output_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2
        assert lines[0] == "0013"
        assert lines[1] == "0093"

    def test_generate_mem_file_padding(self, tmp_path):
        """Test padding to word boundary."""
        bin_file = tmp_path / "test.bin"
        bin_file.write_bytes(b"\x13\x00\x00")  # 3 bytes, needs padding to 4

        output_file = tmp_path / "test.hex"

        result = FirmwareBackend.generate_mem_file(
            bin_file, output_file, format="hex", word_width=32, byte_order="little"
        )

        assert result is True
        content = output_file.read_text().strip()
        # Should be padded with a null byte
        assert content == "00000013"


class TestGccFirmwareBackend:
    """Tests for GccFirmwareBackend."""

    def test_backend_init(self, tmp_path):
        """Test backend initialization."""
        config = {
            "prefix": "riscv64-unknown-elf-",
            "march": "rv64i",
            "mabi": "lp64",
        }
        backend = GccFirmwareBackend(config, tmp_path)

        assert backend.config == config
        assert backend.project_root == tmp_path
        assert backend.get_prefix() == "riscv64-unknown-elf-"

    def test_check_toolchain_not_found(self, tmp_path):
        """Test toolchain check when not found."""
        config = {"prefix": "nonexistent-toolchain-"}
        backend = GccFirmwareBackend(config, tmp_path)

        assert backend.check_toolchain() is False

    @patch("aly.fw_gcc.find_tool")
    def test_check_toolchain_found(self, mock_find_tool, tmp_path):
        """Test toolchain check when found."""
        mock_find_tool.return_value = "/usr/bin/riscv64-unknown-elf-gcc"
        config = {"prefix": "riscv64-unknown-elf-"}
        backend = GccFirmwareBackend(config, tmp_path)

        assert backend.check_toolchain() is True
        mock_find_tool.assert_called_with("riscv64-unknown-elf-gcc")

    def test_get_arch_flags_riscv(self, tmp_path):
        """Test architecture flags for RISC-V."""
        config = {
            "prefix": "riscv64-unknown-elf-",
            "march": "rv64i",
            "mabi": "lp64",
        }
        backend = GccFirmwareBackend(config, tmp_path)
        flags = backend._get_arch_flags()

        assert "-march" in flags
        assert "rv64i" in flags
        assert "-mabi" in flags
        assert "lp64" in flags

    def test_get_arch_flags_arm(self, tmp_path):
        """Test architecture flags for ARM."""
        config = {
            "prefix": "arm-none-eabi-",
            "cpu": "cortex-m4",
        }
        backend = GccFirmwareBackend(config, tmp_path)
        flags = backend._get_arch_flags()

        assert "-mcpu" in flags
        assert "cortex-m4" in flags


class TestFirmwareBackendRegistry:
    """Tests for firmware backend registry."""

    def test_registry_contains_toolchains(self):
        """Test that registry contains expected toolchains."""
        assert "riscv64" in FIRMWARE_BACKENDS
        assert "riscv32" in FIRMWARE_BACKENDS
        assert "arm" in FIRMWARE_BACKENDS

    def test_get_firmware_backend_riscv(self, tmp_path):
        """Test getting RISC-V backend."""
        config = {"prefix": "riscv64-unknown-elf-"}
        backend = get_firmware_backend("riscv64", config, tmp_path)

        assert backend is not None
        assert isinstance(backend, GccFirmwareBackend)

    def test_get_firmware_backend_arm(self, tmp_path):
        """Test getting ARM backend."""
        config = {"prefix": "arm-none-eabi-"}
        backend = get_firmware_backend("arm", config, tmp_path)

        assert backend is not None
        assert isinstance(backend, GccFirmwareBackend)

    def test_get_firmware_backend_unknown_uses_gcc(self, tmp_path):
        """Test that unknown toolchains default to GCC backend."""
        config = {"prefix": "custom-"}
        backend = get_firmware_backend("unknown", config, tmp_path)

        assert backend is not None
        assert isinstance(backend, GccFirmwareBackend)


class TestBuildFirmwareAPI:
    """Tests for build_firmware API function."""

    def test_build_firmware_toolchain_not_found(self, tmp_path):
        """Test build_firmware when toolchain not found."""
        build_config = Mock()
        build_config.name = "test_build"

        tc_config = {"prefix": "nonexistent-toolchain-"}

        result = build_firmware(
            build_config,
            tc_config,
            tmp_path,
            tmp_path / "build",
            toolchain_name="riscv64",
        )

        assert result.success is False
        assert "not found" in result.stderr.lower()


class TestFirmwareCommand:
    """Tests for Firmware command."""

    def test_firmware_command_parser(self):
        """Test firmware command argument parser."""
        from aly.app.firmware import Firmware
        from argparse import ArgumentParser

        parser = ArgumentParser()
        subparsers = parser.add_subparsers()
        fw_parser = Firmware.add_parser(subparsers)

        # Parse with build name
        args = parser.parse_args(["firmware", "test_build"])
        assert args.build == "test_build"

        # Parse with options
        args = parser.parse_args(
            [
                "firmware",
                "test_build",
                "--mem-format",
                "coe",
                "--word-width",
                "16",
                "--byte-order",
                "big",
            ]
        )
        assert args.mem_format == "coe"
        assert args.word_width == 16
        assert args.byte_order == "big"

    def test_firmware_command_no_mem_option(self):
        """Test firmware command --no-mem option."""
        from aly.app.firmware import Firmware
        from argparse import ArgumentParser

        parser = ArgumentParser()
        subparsers = parser.add_subparsers()
        Firmware.add_parser(subparsers)

        args = parser.parse_args(["firmware", "--no-mem"])
        assert args.no_mem is True


class TestFirmwareBuild:
    """Tests for FirmwareBuild dataclass."""

    def test_firmware_build_from_dict_minimal(self):
        """Test FirmwareBuild with minimal data."""
        from aly.config.models import FirmwareBuild

        data = {"name": "bootloader"}
        build = FirmwareBuild.from_dict(data)

        assert build.name == "bootloader"
        assert build.author == ""
        assert build.version == "1.0.0"
        assert build.languages == ["c"]
        assert build.sources == []
        assert build.includes == []
        assert build.linker_script is None
        assert build.toolchain is None

    def test_firmware_build_from_dict_full(self):
        """Test FirmwareBuild with full data."""
        from aly.config.models import FirmwareBuild

        data = {
            "name": "bootloader",
            "author": "Mohamed Aly",
            "version": "2.0.0",
            "languages": ["asm", "c"],
            "sources": ["src/boot.S", "src/main.c"],
            "includes": ["include", "common/include"],
            "linker_script": "linkers/memory.ld",
            "toolchain": "riscv64",
            "defines": {"DEBUG": "1"},
            "flags": {
                "common": ["-fno-builtin"],
                "c": ["-O2"],
                "asm": ["-x"],
                "ld": ["-nostartfiles"],
            },
            "outputs": [
                {"format": "elf", "required": True},
                {"format": "mem", "required": True, "plusarg": "MEM_FILE"},
            ],
            "mem": [
                {"name": "memory.mem", "format": "mem", "word_width": 64, "byte_order": "little"}
            ],
        }
        build = FirmwareBuild.from_dict(data)

        assert build.name == "bootloader"
        assert build.author == "Mohamed Aly"
        assert build.version == "2.0.0"
        assert build.languages == ["asm", "c"]
        assert build.sources == ["src/boot.S", "src/main.c"]
        assert build.includes == ["include", "common/include"]
        assert build.linker_script == "linkers/memory.ld"
        assert build.toolchain == "riscv64"
        assert build.defines == {"DEBUG": "1"}
        assert build.flags.common == ["-fno-builtin"]
        assert build.flags.c == ["-O2"]
        assert len(build.outputs) == 2
        assert build.outputs[0].format == "elf"
        assert build.outputs[1].plusarg == "MEM_FILE"
        assert len(build.mem) == 1
        assert build.mem[0].word_width == 64

    def test_firmware_build_from_list(self):
        """Test FirmwareBuild.from_list()."""
        from aly.config.models import FirmwareBuild

        data = [
            {"name": "build1", "sources": ["a.c"]},
            {"name": "build2", "sources": ["b.c"]},
        ]
        builds = FirmwareBuild.from_list(data)

        assert len(builds) == 2
        assert builds[0].name == "build1"
        assert builds[1].name == "build2"

    def test_firmware_build_to_dict(self):
        """Test FirmwareBuild.to_dict()."""
        from aly.config.models import FirmwareBuild

        build = FirmwareBuild(
            name="test",
            author="Test Author",
            sources=["src/main.c"],
            includes=["include"],
        )
        d = build.to_dict()

        assert d["name"] == "test"
        assert d["author"] == "Test Author"
        assert d["sources"] == ["src/main.c"]
        assert d["includes"] == ["include"]
        # Defaults should not be included
        assert "version" not in d  # version is 1.0.0 (default)
        assert "languages" not in d  # languages is ["c"] (default)

    def test_firmware_build_resolve_files(self, tmp_path):
        """Test FirmwareBuild.resolve_files() with actual files."""
        from aly.config.models import FirmwareBuild

        # Create test files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.c").write_text("int main() {}")
        (src_dir / "boot.S").write_text(".global _start")

        build = FirmwareBuild(
            name="test",
            sources=["src/main.c", "src/boot.S"],
            _manifest_path=tmp_path / "manifest.yaml",
        )

        files = build.resolve_files()
        assert len(files) == 2
        assert any("main.c" in str(f) for f in files)
        assert any("boot.S" in str(f) for f in files)

    def test_firmware_build_get_flags(self):
        """Test flag getter methods."""
        from aly.config.models import FirmwareBuild
        from aly.config.models.helpers import FirmwareFlags

        build = FirmwareBuild(
            name="test",
            flags=FirmwareFlags(
                common=["-fno-builtin"],
                c=["-O2", "-Wall"],
                asm=["-x"],
                ld=["-nostartfiles"],
            ),
        )

        cflags = build.get_all_cflags()
        assert "-fno-builtin" in cflags
        assert "-O2" in cflags
        assert "-Wall" in cflags

        ldflags = build.get_all_ldflags()
        assert "-fno-builtin" in ldflags
        assert "-nostartfiles" in ldflags

        asm_flags = build.get_asm_flags()
        assert "-fno-builtin" in asm_flags
        assert "-x" in asm_flags


class TestFirmwareManifest:
    """Tests for FirmwareManifest with multi-build support."""

    def test_manifest_from_dict_empty_builds(self):
        """Test FirmwareManifest with no builds."""
        from aly.config.models import FirmwareManifest

        data = {
            "name": "my_firmware",
            "type": "firmware",
            "toolchain": "riscv64",
        }
        manifest = FirmwareManifest.from_dict(data)

        assert manifest.name == "my_firmware"
        assert manifest.type == "firmware"
        assert manifest.toolchain == "riscv64"
        assert manifest.builds == []

    def test_manifest_from_dict_with_builds(self):
        """Test FirmwareManifest with builds."""
        from aly.config.models import FirmwareManifest

        data = {
            "name": "my_firmware",
            "type": "firmware",
            "version": "1.0.0",
            "author": "Mohamed Aly",
            "toolchain": "riscv64",
            "builds": [
                {"name": "bootloader", "sources": ["src/boot.S"]},
                {"name": "application", "sources": ["src/main.c"]},
            ],
        }
        manifest = FirmwareManifest.from_dict(data)

        assert manifest.name == "my_firmware"
        assert len(manifest.builds) == 2
        assert manifest.builds[0].name == "bootloader"
        assert manifest.builds[1].name == "application"

    def test_manifest_get_build(self):
        """Test FirmwareManifest.get_build()."""
        from aly.config.models import FirmwareManifest, FirmwareBuild

        manifest = FirmwareManifest(
            name="test",
            builds=[
                FirmwareBuild(name="build1"),
                FirmwareBuild(name="build2"),
            ],
        )

        assert manifest.get_build("build1").name == "build1"
        assert manifest.get_build("build2").name == "build2"
        assert manifest.get_build("nonexistent") is None

    def test_manifest_add_build(self):
        """Test FirmwareManifest.add_build()."""
        from aly.config.models import FirmwareManifest, FirmwareBuild

        manifest = FirmwareManifest(name="test")
        build = FirmwareBuild(name="new_build")

        assert manifest.add_build(build) is True
        assert len(manifest.builds) == 1
        assert manifest.get_build("new_build") is not None

        # Adding duplicate should fail
        duplicate = FirmwareBuild(name="new_build")
        assert manifest.add_build(duplicate) is False
        assert len(manifest.builds) == 1

    def test_manifest_get_build_names(self):
        """Test FirmwareManifest.get_build_names()."""
        from aly.config.models import FirmwareManifest, FirmwareBuild

        manifest = FirmwareManifest(
            name="test",
            builds=[
                FirmwareBuild(name="build1"),
                FirmwareBuild(name="build2"),
                FirmwareBuild(name="build3"),
            ],
        )

        names = manifest.get_build_names()
        assert names == ["build1", "build2", "build3"]

    def test_manifest_to_dict(self):
        """Test FirmwareManifest.to_dict()."""
        from aly.config.models import FirmwareManifest, FirmwareBuild

        manifest = FirmwareManifest(
            name="my_firmware",
            version="1.0.0",
            author="Test",
            toolchain="riscv64",
            builds=[FirmwareBuild(name="bootloader", sources=["src/boot.S"])],
        )

        d = manifest.to_dict()
        assert d["name"] == "my_firmware"
        assert d["type"] == "firmware"
        assert d["toolchain"] == "riscv64"
        assert len(d["builds"]) == 1
        assert d["builds"][0]["name"] == "bootloader"

    def test_manifest_validate_no_builds_warning(self):
        """Test validation warns on empty builds."""
        from aly.config.models import FirmwareManifest
        from aly.config.models.helpers import ValidationLevel

        manifest = FirmwareManifest(name="test")
        messages = manifest.validate()

        warnings = [m for m in messages if m.level == ValidationLevel.WARNING]
        assert any("no builds" in m.message.lower() for m in warnings)

    def test_manifest_validate_build_no_sources_error(self):
        """Test validation errors on build without sources."""
        from aly.config.models import FirmwareManifest, FirmwareBuild
        from aly.config.models.helpers import ValidationLevel

        manifest = FirmwareManifest(
            name="test",
            builds=[FirmwareBuild(name="empty_build", sources=[])],
        )
        messages = manifest.validate()

        errors = [m for m in messages if m.level == ValidationLevel.ERROR]
        assert any("source file" in m.message.lower() for m in errors)

    def test_manifest_load_and_save(self, tmp_path):
        """Test loading and saving manifest."""
        from aly.config.models import FirmwareManifest, FirmwareBuild

        manifest_path = tmp_path / "manifest.yaml"

        # Create and save
        manifest = FirmwareManifest(
            name="my_firmware",
            toolchain="riscv64",
            builds=[
                FirmwareBuild(name="build1", sources=["src/main.c"]),
            ],
        )
        manifest.save(manifest_path)

        # Load and verify
        loaded = FirmwareManifest.load(manifest_path)
        assert loaded.name == "my_firmware"
        assert loaded.toolchain == "riscv64"
        assert len(loaded.builds) == 1
        assert loaded.builds[0].name == "build1"
