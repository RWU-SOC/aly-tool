# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Configuration management for ALY."""

import configparser
import os
from pathlib import Path
from typing import Optional


class Configuration:
    """Configuration manager for ALY.

    Reads configuration from:
    1. System-wide: ~/.alyconfig
    2. Project-level: <topdir>/.aly/config
    3. Environment variables: ALY_*
    """

    def __init__(self, topdir: Optional[Path] = None):
        self.topdir = topdir or Path.cwd()
        self._config = configparser.ConfigParser()
        self._load()

    def _load(self):
        """Load configuration from all sources."""
        # System-wide config
        system_config = Path.home() / ".alyconfig"
        if system_config.exists():
            self._config.read(system_config)

        # Project config
        project_config = self.topdir / ".aly" / "config"
        if project_config.exists():
            self._config.read(project_config)

    def get(self, key: str, fallback=None):
        """Get a configuration value.

        Args:
            key: Config key in format 'section.option'
            fallback: Default value if key not found

        Returns:
            Configuration value or fallback
        """
        # Check environment variable first
        env_key = f'ALY_{key.replace(".", "_").upper()}'
        env_val = os.getenv(env_key)
        if env_val is not None:
            return env_val

        # Parse section.option
        parts = key.split(".", 1)
        if len(parts) != 2:
            return fallback

        section, option = parts
        return self._config.get(section, option, fallback=fallback)

    def set(self, key: str, value: str, scope="project"):
        """Set a configuration value.

        Args:
            key: Config key in format 'section.option'
            value: Value to set
            scope: 'system' or 'project'
        """
        parts = key.split(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid config key: {key}")

        section, option = parts

        if not self._config.has_section(section):
            self._config.add_section(section)

        self._config.set(section, option, value)

        # Save to file
        if scope == "system":
            config_file = Path.home() / ".alyconfig"
        else:
            config_file = self.topdir / ".aly" / "config"
            config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w") as f:
            self._config.write(f)
