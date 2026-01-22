# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Tests for ALY utility functions."""

import pytest
from pathlib import Path
from aly.util import find_aly_root, find_tool


def test_find_aly_root_current_dir(temp_project):
    """Test finding ALY root in current directory."""
    root = find_aly_root(temp_project)
    assert root == temp_project


def test_find_aly_root_subdirectory(temp_project):
    """Test finding ALY root from subdirectory."""
    subdir = temp_project / "firmware" / "src"
    subdir.mkdir(parents=True)

    root = find_aly_root(subdir)
    assert root == temp_project


def test_find_aly_root_not_found(tmp_path):
    """Test when ALY root is not found."""
    no_aly_dir = tmp_path / "not_aly"
    no_aly_dir.mkdir()

    root = find_aly_root(no_aly_dir)
    assert root is None


def test_find_tool_python():
    """Test finding Python (should exist)."""
    python = find_tool("python")
    assert python is not None
