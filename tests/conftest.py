# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Pytest configuration for ALY tests."""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary ALY project for testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create .aly directory
    aly_dir = project_dir / ".aly"
    aly_dir.mkdir()
    (aly_dir / "config").write_text("")

    # Create basic structure
    (project_dir / "firmware").mkdir()
    (project_dir / "rtl").mkdir()

    yield project_dir

    # Cleanup
    shutil.rmtree(project_dir, ignore_errors=True)


@pytest.fixture
def mock_toolchain(monkeypatch):
    """Mock toolchain availability."""

    def mock_find_tool(name):
        if "riscv" in name or "xvlog" in name:
            return f"/mock/bin/{name}"
        return None

    monkeypatch.setattr("aly.util.find_tool", mock_find_tool)
    return mock_find_tool
