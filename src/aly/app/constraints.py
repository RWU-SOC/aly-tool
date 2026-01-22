# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Constraint management for ALY.

This module provides commands for managing design constraints including
timing, I/O, and physical constraints with validation and generation.

Integrates with ProjectConfig for constraint file discovery.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from aly import log
from aly.commands import AlyCommand
from aly.util import find_aly_root
from aly.config import ProjectConfig


@dataclass
class ConstraintSet:
    """A constraint set referencing external XDC/SDC files."""

    name: str
    target: str  # FPGA part or board
    files: List[str] = field(default_factory=list)  # Constraint file paths
    description: str = ""


class ConstraintManager:
    """Manager for design constraints.

    Works with ProjectConfig for constraint discovery and integrates
    with the .aly/constraints.yaml configuration.
    """

    def __init__(self, project_root: Path, config: Optional[ProjectConfig] = None):
        self.project_root = project_root
        self.config = config
        # Load from .aly/constraints.yaml (NEW location)
        self.constraints_yaml = project_root / ".aly" / "constraints.yaml"
        self._constraint_sets: Dict[str, ConstraintSet] = {}

    def init(self):
        """Initialize .aly/constraints.yaml with template."""
        aly_dir = self.project_root / ".aly"
        aly_dir.mkdir(parents=True, exist_ok=True)

        # Create template YAML with new schema
        if not self.constraints_yaml.exists():
            template = {
                "# Design Constraints Configuration": None,
                "sets": {
                    "default": {
                        "target": "xc7a100tcsg324-1",
                        "files": ["constraints/default.xdc"],
                        "description": "Default FPGA constraints",
                    }
                }
            }
            with open(self.constraints_yaml, "w") as f:
                yaml.dump(template, f, default_flow_style=False, sort_keys=False)

        log.inf(f"Created constraints configuration: {self.constraints_yaml}")

    def load(self) -> bool:
        """Load constraints from .aly/constraints.yaml (new schema only)."""
        if not self.constraints_yaml.exists():
            return False

        try:
            with open(self.constraints_yaml) as f:
                data = yaml.safe_load(f)

            # Only support new schema: sets: { name: { target, files, description } }
            for name, cdata in data.get("sets", {}).items():
                self._constraint_sets[name] = ConstraintSet(
                    name=name,
                    target=cdata.get("target", ""),
                    files=cdata.get("files", []),
                    description=cdata.get("description", ""),
                )

            return True
        except Exception as e:
            log.err(f"Failed to load constraints: {e}")
            return False

    def get_constraint_files(self, name: str) -> List[Path]:
        """Get constraint files for a named constraint set.

        Args:
            name: Constraint set name

        Returns:
            List of resolved constraint file paths
        """
        if name not in self._constraint_sets:
            return []

        cs = self._constraint_sets[name]
        files = []

        for f in cs.files:
            p = Path(f)
            if not p.is_absolute():
                p = self.project_root / p
            if p.exists():
                files.append(p)
            else:
                log.wrn(f"Constraint file not found: {f}")

        return files


    def validate(self, constraint_set: str) -> List[str]:
        """Validate constraint set and return list of issues."""
        issues = []

        if constraint_set not in self._constraint_sets:
            return [f"Constraint set not found: {constraint_set}"]

        cs = self._constraint_sets[constraint_set]

        # Check constraint files exist
        if not cs.files:
            issues.append("WARNING: No constraint files specified")

        for f in cs.files:
            p = Path(f)
            if not p.is_absolute():
                p = self.project_root / p
            if not p.exists():
                issues.append(f"ERROR: Constraint file not found: {f}")

        return issues

    def get_constraint_sets(self) -> List[str]:
        """Get list of available constraint sets."""
        return list(self._constraint_sets.keys())


class Constraints(AlyCommand):
    """Constraint management command."""

    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            "constraints", help="manage design constraints"
        )
        subparsers = parser.add_subparsers(dest="const_cmd", help="constraint commands")

        # init - initialize constraints
        init_parser = subparsers.add_parser(
            "init", help="initialize constraints directory"
        )

        # list - list constraint sets
        list_parser = subparsers.add_parser("list", help="list constraint sets")
        list_parser.add_argument("--json", action="store_true", help="output as JSON")

        # show - show constraint details
        show_parser = subparsers.add_parser("show", help="show constraint set details")
        show_parser.add_argument("name", help="constraint set name")
        show_parser.add_argument("--json", action="store_true", help="output as JSON")

        # validate - validate constraints
        val_parser = subparsers.add_parser("validate", help="validate constraints")
        val_parser.add_argument(
            "name", nargs="?", help="constraint set name (all if not specified)"
        )
        val_parser.add_argument(
            "--strict", action="store_true", help="fail on warnings"
        )

        return parser

    def run(self, args, unknown_args):
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        # Load project config if available
        config = None
        try:
            config = ProjectConfig.load(project_root)
        except Exception:
            pass  # Config not required for all commands

        manager = ConstraintManager(project_root, config)

        if args.const_cmd == "init":
            return self._cmd_init(manager)
        elif args.const_cmd == "list":
            return self._cmd_list(manager, args)
        elif args.const_cmd == "show":
            return self._cmd_show(manager, args)
        elif args.const_cmd == "validate":
            return self._cmd_validate(manager, args)
        else:
            # Default: show summary
            return self._cmd_summary(manager)

    def _cmd_init(self, manager: ConstraintManager) -> int:
        """Initialize constraints."""
        log.banner("Initializing Constraints")
        manager.init()
        log.success("Constraints directory initialized")
        log.inf(f"Edit constraints at: {manager.constraints_yaml}")
        return 0

    def _cmd_summary(self, manager: ConstraintManager) -> int:
        """Show constraints summary."""
        if not manager.load():
            log.inf(
                "No constraints found. Run 'aly constraints init' to create templates."
            )
            return 0

        sets = manager.get_constraint_sets()
        log.banner("Constraints Summary")
        print(f"Constraint sets: {len(sets)}")
        for name in sets:
            cs = manager._constraint_sets[name]
            print(f"  {name}: {len(cs.files)} files ({cs.target})")
            if cs.description:
                print(f"    {cs.description}")
        return 0

    def _cmd_list(self, manager: ConstraintManager, args) -> int:
        """List constraint sets."""
        if not manager.load():
            log.wrn("No constraints found")
            return 0

        if args.json:
            data = [
                {
                    "name": name,
                    "target": cs.target,
                    "file_count": len(cs.files),
                    "description": cs.description,
                }
                for name, cs in manager._constraint_sets.items()
            ]
            print(json.dumps(data, indent=2))
        else:
            print(f"{'Name':<20} {'Target':<25} {'Files':<10} {'Description':<30}")
            print("-" * 85)
            for name, cs in manager._constraint_sets.items():
                desc = cs.description[:28] + ".." if len(cs.description) > 30 else cs.description
                print(
                    f"{name:<20} {cs.target:<25} {len(cs.files):<10} {desc:<30}"
                )

        return 0

    def _cmd_show(self, manager: ConstraintManager, args) -> int:
        """Show constraint set details."""
        if not manager.load():
            self.die("No constraints found")

        if args.name not in manager._constraint_sets:
            self.die(f"Constraint set not found: {args.name}")

        cs = manager._constraint_sets[args.name]

        if args.json:
            data = {
                "name": cs.name,
                "target": cs.target,
                "files": cs.files,
                "description": cs.description,
            }
            print(json.dumps(data, indent=2))
        else:
            log.banner(f"Constraint Set: {cs.name}")
            print(f"Target: {cs.target}")
            if cs.description:
                print(f"Description: {cs.description}")

            if cs.files:
                print("\nConstraint Files:")
                for f in cs.files:
                    p = Path(f)
                    if not p.is_absolute():
                        p = manager.project_root / p
                    exists = "[OK]" if p.exists() else "[MISSING]"
                    print(f"  {exists} {f}")

        return 0


    def _cmd_validate(self, manager: ConstraintManager, args) -> int:
        """Validate constraints."""
        if not manager.load():
            self.die("No constraints found")

        log.banner("Validating Constraints")

        sets_to_check = [args.name] if args.name else manager.get_constraint_sets()
        has_errors = False

        for name in sets_to_check:
            issues = manager.validate(name)
            if issues:
                print(f"\n{name}:")
                for issue in issues:
                    if issue.startswith("ERROR"):
                        log.err(f"  {issue}")
                        has_errors = True
                    else:
                        log.wrn(f"  {issue}")
                        if args.strict:
                            has_errors = True
            else:
                log.success(f"{name}: OK")

        if has_errors:
            self.die("Validation failed")

        return 0

