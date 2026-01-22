# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Command base class and extension system for ALY."""

import abc
import argparse
import importlib.util
import itertools
import os
import sys
from pathlib import Path
from typing import NoReturn, Optional

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

import yaml

from aly import log
from aly.configuration import Configuration


class CommandError(RuntimeError):
    """Indicates that a command failed."""

    def __init__(self, returncode=1):
        super().__init__()
        self.returncode = returncode


class ExtensionCommandError(CommandError):
    """Exception for badly defined extension commands."""

    def __init__(self, **kwargs):
        self.hint = kwargs.pop("hint", None)
        super().__init__(**kwargs)


class AlyCommand(abc.ABC):
    """Base class for ALY commands.

    All ALY commands (built-in and extensions) inherit from this class.
    """

    def __init__(self):
        self.name = self.__class__.__name__.lower()
        self.topdir = None
        self.config = None

    @staticmethod
    @abc.abstractmethod
    def add_parser(parser_adder):
        """Add the command's subparser to a parser_adder.

        Args:
            parser_adder: A return value of argparse.add_subparsers()

        Returns:
            argparse.ArgumentParser for the command
        """

    @abc.abstractmethod
    def run(self, args, unknown_args):
        """Run the command.

        Args:
            args: Parsed arguments from argparse
            unknown_args: List of unknown arguments

        Returns:
            Command return code (0 for success)
        """

    def dbg(self, *args, **kwargs):
        """Log a debug message."""
        log.dbg(*args, **kwargs)

    def inf(self, *args, **kwargs):
        """Log an info message."""
        log.inf(*args, **kwargs)

    def wrn(self, *args, **kwargs):
        """Log a warning message."""
        log.wrn(*args, **kwargs)

    def err(self, *args, **kwargs):
        """Log an error message."""
        log.err(*args, **kwargs)

    def die(self, *args, **kwargs) -> NoReturn:
        """Log an error and exit."""
        log.die(*args, **kwargs)


# Extension command caching
_EXT_MODULES_CACHE = {}
_EXT_MODULES_NAME_IT = (f"aly.commands.ext.cmd_{i}" for i in itertools.count(1))


def extension_commands(project_path: Optional[Path] = None):
    """Discover and return extension commands.

    Looks for:
    1. .aly/commands.yml in project directory
    2. Custom command directories specified in config

    Args:
        project_path: Path to project root (uses cwd if None)

    Returns:
        List of AlyCommand subclass instances
    """
    commands = []

    if project_path is None:
        project_path = Path.cwd()

    # Look for .aly/commands.yml in project
    commands_file = project_path / ".aly" / "commands.yml"
    if commands_file.exists():
        commands.extend(_load_commands_yml(commands_file, project_path))

    # Look for custom command paths in config
    try:
        config = Configuration(topdir=project_path)
        custom_paths = config.get("aly.commands-path", fallback="").split(";")
        for path in custom_paths:
            if path:
                path = Path(path).expanduser()
                if path.is_file() and path.suffix == ".yml":
                    commands.extend(_load_commands_yml(path, project_path))
    except Exception:
        pass  # Config not available, skip

    return commands


def _load_commands_yml(yml_path: Path, project_path: Path):
    """Load commands from a YAML file."""
    commands = []

    try:
        with open(yml_path) as f:
            data = yaml.load(f, Loader=SafeLoader)

        if not data or "aly-commands" not in data:
            return commands

        for cmd_spec in data["aly-commands"]:
            file_path = cmd_spec.get("file")
            if not file_path:
                continue

            # Resolve relative to YAML file location
            if not Path(file_path).is_absolute():
                file_path = (yml_path.parent / file_path).resolve()
            else:
                file_path = Path(file_path)

            if not file_path.exists():
                log.wrn(f"Extension command file not found: {file_path}")
                continue

            # Import the module
            module = _import_extension_module(file_path)

            # Extract commands from module
            for cmd_def in cmd_spec.get("commands", []):
                cmd_name = cmd_def.get("name")
                cmd_class = cmd_def.get("class")

                if not cmd_name or not cmd_class:
                    continue

                if not hasattr(module, cmd_class):
                    log.wrn(f"Class {cmd_class} not found in {file_path}")
                    continue

                cls = getattr(module, cmd_class)
                if not issubclass(cls, AlyCommand):
                    log.wrn(f"{cmd_class} does not inherit from AlyCommand")
                    continue

                try:
                    commands.append(cls())
                except Exception as e:
                    log.wrn(f"Failed to instantiate {cmd_class}: {e}")

    except Exception as e:
        log.wrn(f"Failed to load commands from {yml_path}: {e}")

    return commands


def _import_extension_module(path: Path):
    """Import a Python module from a file path."""
    path_str = str(path)

    # Check cache
    if path_str in _EXT_MODULES_CACHE:
        return _EXT_MODULES_CACHE[path_str]

    # Generate unique module name
    module_name = next(_EXT_MODULES_NAME_IT)

    # Import the module
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ExtensionCommandError(hint=f"Cannot load module from {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Cache it
    _EXT_MODULES_CACHE[path_str] = module

    return module
