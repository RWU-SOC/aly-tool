# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Tests for configuration management."""

import pytest
from pathlib import Path
from aly.configuration import Configuration


def test_configuration_basic(temp_project):
    """Test basic configuration."""
    config = Configuration(topdir=temp_project)

    # Set a value
    config.set("test.key", "value", scope="project")

    # Read it back
    assert config.get("test.key") == "value"

    # Check file was created
    config_file = temp_project / ".aly" / "config"
    assert config_file.exists()


def test_configuration_fallback(temp_project):
    """Test configuration fallback."""
    config = Configuration(topdir=temp_project)

    # Non-existent key with fallback
    value = config.get("nonexistent.key", fallback="default")
    assert value == "default"


def test_configuration_environment(temp_project, monkeypatch):
    """Test environment variable override."""
    monkeypatch.setenv("ALY_TEST_KEY", "env_value")

    config = Configuration(topdir=temp_project)
    config.set("test.key", "file_value", scope="project")

    # Environment should override file
    assert config.get("test.key") == "env_value"
