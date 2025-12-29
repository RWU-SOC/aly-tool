# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Tests for ALY commands."""

import pytest
from pathlib import Path
from aly.app import Info, Clean, Version
from aly.app.init import Init


def test_info_command(temp_project, capsys):
    """Test info command."""
    cmd = Info()
    cmd.topdir = temp_project
    
    result = cmd.run(type('Args', (), {})(), [])
    assert result == 0
    
    captured = capsys.readouterr()
    assert "ALY Configuration" in captured.out


def test_clean_command(temp_project, monkeypatch):
    """Test clean command."""
    # Create .aly directory
    (temp_project / ".aly").mkdir(exist_ok=True)
    
    # Create build directory
    build_dir = temp_project / ".aly_build"
    build_dir.mkdir()
    (build_dir / "test.txt").write_text("test")
    
    # Mock find_aly_root in the Clean command module
    import aly.app
    monkeypatch.setattr(aly.app, 'find_aly_root', lambda: temp_project)
    
    cmd = Clean()
    result = cmd.run(type('Args', (), {})(), [])
    assert result == 0
    assert not build_dir.exists()


def test_version_command(capsys):
    """Test version command."""
    cmd = Version()
    
    result = cmd.run(type('Args', (), {})(), [])
    assert result == 0
    
    captured = capsys.readouterr()
    assert "ALY version" in captured.out


def test_init_command(tmp_path, capsys):
    """Test init command."""
    project_dir = tmp_path / "new_project"
    
    cmd = Init()
    args = type('Args', (), {
        'path': str(project_dir),
        'template': 'soc',
        'list_templates': False
    })()
    
    result = cmd.run(args, [])
    assert result == 0
    
    # Check structure was created
    assert (project_dir / ".aly").exists()
    assert (project_dir / "rtl").exists()
    assert (project_dir / "firmware").exists()
    assert (project_dir / "README.md").exists()


def test_init_list_templates(capsys):
    """Test listing templates."""
    cmd = Init()
    args = type('Args', (), {
        'path': '.',
        'template': 'soc',
        'list_templates': True
    })()
    
    result = cmd.run(args, [])
    assert result == 0
    
    captured = capsys.readouterr()
    assert "soc" in captured.out
    assert "firmware-only" in captured.out
