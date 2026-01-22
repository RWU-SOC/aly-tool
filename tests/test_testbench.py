# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Tests for testbench manifest classes."""

import pytest
import tempfile
from pathlib import Path

from aly.config.models.testbench import Testbench, TestSuite, TestbenchManifest


class TestTestbench:
    """Tests for Testbench dataclass."""

    def test_testbench_defaults(self):
        """Test Testbench default values."""
        tb = Testbench(name="tb_alu")
        assert tb.name == "tb_alu"
        assert tb.author == ""
        assert tb.version == "1.0.0"
        assert tb.description == ""
        assert tb.language == "systemverilog"
        assert tb.top is None
        assert tb.files == []
        assert tb.includes == []
        assert tb.defines == {}
        assert tb.dependencies == []
        assert tb.default_timeout == 10000
        assert tb.plusargs == {}
        assert tb.tags == []

    def test_testbench_top_module_property(self):
        """Test top_module property defaults to name."""
        tb = Testbench(name="tb_alu")
        assert tb.top_module == "tb_alu"

        tb_with_top = Testbench(name="tb_alu", top="alu_testbench")
        assert tb_with_top.top_module == "alu_testbench"

    def test_testbench_from_dict(self):
        """Test Testbench.from_dict() parsing."""
        data = {
            "name": "tb_mux",
            "author": "John Doe",
            "version": "2.0.0",
            "description": "Testbench for mux module",
            "language": "verilog",
            "top": "tb_mux_top",
            "files": ["tb_mux.sv", "mux.sv"],
            "includes": ["include"],
            "defines": {"DEBUG": "1"},
            "dependencies": [
                {"name": "mux_rtl", "type": "rtl"},
                {"name": "firmware_build", "type": "firmware"},
            ],
            "default_timeout": 5000,
            "plusargs": {"SEED": "12345"},
            "tags": ["smoke", "unit"],
        }

        tb = Testbench.from_dict(data)

        assert tb.name == "tb_mux"
        assert tb.author == "John Doe"
        assert tb.version == "2.0.0"
        assert tb.description == "Testbench for mux module"
        assert tb.language == "verilog"
        assert tb.top == "tb_mux_top"
        assert tb.files == ["tb_mux.sv", "mux.sv"]
        assert tb.includes == ["include"]
        assert tb.defines == {"DEBUG": "1"}
        assert len(tb.dependencies) == 2
        assert tb.default_timeout == 5000
        assert tb.plusargs == {"SEED": "12345"}
        assert tb.tags == ["smoke", "unit"]

    def test_testbench_from_dict_string_deps(self):
        """Test parsing string dependencies (shorthand)."""
        data = {
            "name": "tb_test",
            "dependencies": ["module_a", "module_b"],
        }

        tb = Testbench.from_dict(data)

        assert len(tb.dependencies) == 2
        assert tb.dependencies[0] == {"name": "module_a", "type": "rtl", "required": True}
        assert tb.dependencies[1] == {"name": "module_b", "type": "rtl", "required": True}

    def test_testbench_get_rtl_deps(self):
        """Test get_rtl_deps() filters by type."""
        tb = Testbench(
            name="tb_test",
            dependencies=[
                {"name": "rtl_module", "type": "rtl"},
                {"name": "fw_build", "type": "firmware"},
                {"name": "another_rtl", "type": "rtl"},
            ],
        )

        rtl_deps = tb.get_rtl_deps()
        assert len(rtl_deps) == 2
        assert rtl_deps[0]["name"] == "rtl_module"
        assert rtl_deps[1]["name"] == "another_rtl"

    def test_testbench_get_firmware_deps(self):
        """Test get_firmware_deps() filters by type."""
        tb = Testbench(
            name="tb_test",
            dependencies=[
                {"name": "rtl_module", "type": "rtl"},
                {"name": "fw_build", "type": "firmware"},
                {"name": "another_fw", "type": "firmware"},
            ],
        )

        fw_deps = tb.get_firmware_deps()
        assert len(fw_deps) == 2
        assert fw_deps[0]["name"] == "fw_build"
        assert fw_deps[1]["name"] == "another_fw"

    def test_testbench_to_dict(self):
        """Test Testbench.to_dict() serialization."""
        tb = Testbench(
            name="tb_alu",
            author="Test Author",
            description="Test description",
            files=["tb_alu.sv"],
            tags=["smoke"],
        )

        d = tb.to_dict()

        assert d["name"] == "tb_alu"
        assert d["author"] == "Test Author"
        assert d["description"] == "Test description"
        assert d["files"] == ["tb_alu.sv"]
        assert d["tags"] == ["smoke"]
        # Default values should not be in output
        assert "version" not in d  # version is 1.0.0 (default)
        assert "language" not in d  # language is systemverilog (default)

    def test_testbench_resolve_files(self, tmp_path):
        """Test file resolution with manifest path."""
        # Create test files
        tb_file = tmp_path / "tb_test.sv"
        tb_file.write_text("// testbench")

        manifest_path = tmp_path / "manifest.yaml"

        tb = Testbench(
            name="tb_test",
            files=["tb_test.sv"],
            _manifest_path=manifest_path,
        )

        files = tb.resolve_files()
        assert len(files) == 1
        assert files[0] == tb_file


class TestTestSuite:
    """Tests for TestSuite dataclass."""

    def test_testsuite_defaults(self):
        """Test TestSuite default values."""
        suite = TestSuite(name="regression_suite")
        assert suite.name == "regression_suite"
        assert suite.description == ""
        assert suite.testbenches == []
        assert suite.parallel == 1
        assert suite.timeout == 60
        assert suite.stop_on_fail is False

    def test_testsuite_from_dict(self):
        """Test TestSuite.from_dict() parsing."""
        data = {
            "name": "alu_suite",
            "description": "ALU test suite",
            "testbenches": ["tb_alu", "tb_mux"],
            "parallel": 4,
            "timeout": 120,
            "stop_on_fail": True,
        }

        suite = TestSuite.from_dict(data)

        assert suite.name == "alu_suite"
        assert suite.description == "ALU test suite"
        assert suite.testbenches == ["tb_alu", "tb_mux"]
        assert suite.parallel == 4
        assert suite.timeout == 120
        assert suite.stop_on_fail is True

    def test_testsuite_to_dict(self):
        """Test TestSuite.to_dict() serialization."""
        suite = TestSuite(
            name="test_suite",
            description="Test suite description",
            testbenches=["tb_a", "tb_b"],
            parallel=2,
        )

        d = suite.to_dict()

        assert d["name"] == "test_suite"
        assert d["testbenches"] == ["tb_a", "tb_b"]
        assert d["description"] == "Test suite description"
        assert d["parallel"] == 2
        # Default values should not be in output
        assert "timeout" not in d  # timeout is 60 (default)
        assert "stop_on_fail" not in d  # stop_on_fail is False (default)


class TestTestbenchManifest:
    """Tests for TestbenchManifest dataclass."""

    def test_manifest_defaults(self):
        """Test TestbenchManifest default values."""
        manifest = TestbenchManifest()
        assert manifest.name == "testbench"
        assert manifest.type == "testbench"
        assert manifest.version == "1.0.0"
        assert manifest.description == ""
        assert manifest.author == ""
        assert manifest.license == ""
        assert manifest.testbenches == []
        assert manifest.testsuites == []

    def test_manifest_from_dict_with_testbenches(self):
        """Test parsing manifest with testbenches list."""
        data = {
            "name": "alu_testbenches",
            "type": "testbench",
            "version": "1.0.0",
            "description": "ALU testbench collection",
            "author": "John Doe",
            "testbenches": [
                {"name": "tb_alu", "files": ["tb_alu.sv"]},
                {"name": "tb_mux", "files": ["tb_mux.sv"]},
            ],
            "testsuites": [
                {
                    "name": "full_suite",
                    "testbenches": ["tb_alu", "tb_mux"],
                }
            ],
        }

        manifest = TestbenchManifest.from_dict(data)

        assert manifest.name == "alu_testbenches"
        assert manifest.type == "testbench"
        assert manifest.author == "John Doe"
        assert len(manifest.testbenches) == 2
        assert manifest.testbenches[0].name == "tb_alu"
        assert manifest.testbenches[1].name == "tb_mux"
        assert len(manifest.testsuites) == 1
        assert manifest.testsuites[0].name == "full_suite"

    def test_manifest_get_testbench(self):
        """Test get_testbench() lookup."""
        manifest = TestbenchManifest(
            testbenches=[
                Testbench(name="tb_a"),
                Testbench(name="tb_b"),
            ]
        )

        tb = manifest.get_testbench("tb_a")
        assert tb is not None
        assert tb.name == "tb_a"

        tb_missing = manifest.get_testbench("tb_missing")
        assert tb_missing is None

    def test_manifest_get_testsuite(self):
        """Test get_testsuite() lookup."""
        manifest = TestbenchManifest(
            testsuites=[
                TestSuite(name="suite_a"),
                TestSuite(name="suite_b"),
            ]
        )

        suite = manifest.get_testsuite("suite_a")
        assert suite is not None
        assert suite.name == "suite_a"

        suite_missing = manifest.get_testsuite("suite_missing")
        assert suite_missing is None

    def test_manifest_add_testbench(self):
        """Test add_testbench() method."""
        manifest = TestbenchManifest()

        tb1 = Testbench(name="tb_a")
        assert manifest.add_testbench(tb1) is True
        assert len(manifest.testbenches) == 1

        # Duplicate should fail
        tb2 = Testbench(name="tb_a")
        assert manifest.add_testbench(tb2) is False
        assert len(manifest.testbenches) == 1

    def test_manifest_add_testsuite(self):
        """Test add_testsuite() method."""
        manifest = TestbenchManifest()

        suite1 = TestSuite(name="suite_a")
        assert manifest.add_testsuite(suite1) is True
        assert len(manifest.testsuites) == 1

        # Duplicate should fail
        suite2 = TestSuite(name="suite_a")
        assert manifest.add_testsuite(suite2) is False
        assert len(manifest.testsuites) == 1

    def test_manifest_validate_no_testbenches(self):
        """Test validation warning for empty manifest."""
        manifest = TestbenchManifest()
        messages = manifest.validate()

        # Should have warning about no testbenches
        warnings = [m for m in messages if m.level.value == "warning"]
        assert len(warnings) >= 1

    def test_manifest_validate_missing_files(self):
        """Test validation error for testbench without files."""
        manifest = TestbenchManifest(
            testbenches=[Testbench(name="tb_no_files", files=[])]
        )
        messages = manifest.validate()

        errors = [m for m in messages if m.level.value == "error"]
        assert len(errors) >= 1
        assert "requires at least one file" in errors[0].message

    def test_manifest_validate_invalid_language(self):
        """Test validation error for invalid language."""
        manifest = TestbenchManifest(
            testbenches=[Testbench(name="tb_test", files=["test.sv"], language="invalid")]
        )
        messages = manifest.validate()

        errors = [m for m in messages if m.level.value == "error"]
        assert any("invalid language" in e.message for e in errors)

    def test_manifest_to_dict(self):
        """Test to_dict() serialization."""
        manifest = TestbenchManifest(
            name="test_manifest",
            description="Test description",
            testbenches=[Testbench(name="tb_a", files=["tb_a.sv"])],
            testsuites=[TestSuite(name="suite_a", testbenches=["tb_a"])],
        )

        d = manifest.to_dict()

        assert d["name"] == "test_manifest"
        assert d["type"] == "testbench"
        assert d["description"] == "Test description"
        assert len(d["testbenches"]) == 1
        assert len(d["testsuites"]) == 1

    def test_manifest_load_save_roundtrip(self, tmp_path):
        """Test load/save roundtrip."""
        manifest_path = tmp_path / "manifest.yaml"

        # Create and save
        manifest = TestbenchManifest(
            name="roundtrip_test",
            description="Roundtrip test",
            testbenches=[
                Testbench(name="tb_a", files=["tb_a.sv"]),
            ],
            testsuites=[
                TestSuite(name="suite_a", testbenches=["tb_a"]),
            ],
        )
        manifest.save(manifest_path)

        # Load and verify
        loaded = TestbenchManifest.load(manifest_path)

        assert loaded.name == "roundtrip_test"
        assert loaded.description == "Roundtrip test"
        assert len(loaded.testbenches) == 1
        assert loaded.testbenches[0].name == "tb_a"
        assert len(loaded.testsuites) == 1
        assert loaded.testsuites[0].name == "suite_a"
