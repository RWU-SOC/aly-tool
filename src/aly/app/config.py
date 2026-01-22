# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Configuration management command."""

import json
import yaml
from pathlib import Path

from aly import log
from aly.commands import AlyCommand
from aly.util import find_aly_root
from aly.config import ProjectConfig
# from aly.config.loader import ConfigurationError


class Config(AlyCommand):
    """
    Manage project configuration.

    View, validate, and edit project configuration stored in .aly/ directory.

    Examples:
        aly config                      # Show configuration summary
        aly config show                 # Show full configuration
        aly config show rtl             # Show RTL configuration
        aly config validate             # Validate configuration
        aly config list                 # List configuration files
    """

    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            "config",
            help="manage project configuration",
            description="View, validate, and edit project configuration",
        )

        subparsers = parser.add_subparsers(dest="config_cmd", help="config commands")

        # Show command
        show_parser = subparsers.add_parser("show", help="show configuration")
        show_parser.add_argument(
            "section",
            nargs="?",
            help="configuration section (rtl, tb, sim, synth, etc.)",
        )
        show_parser.add_argument("--json", action="store_true", help="output as JSON")

        # Validate command
        validate_parser = subparsers.add_parser(
            "validate", help="validate configuration"
        )
        validate_parser.add_argument(
            "--strict", action="store_true", help="fail on warnings"
        )

        # List command
        _list_parser = subparsers.add_parser("list", help="list configuration files")

        return parser

    def run(self, args, unknown_args):
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project (no .aly directory found)")

        cmd = getattr(args, "config_cmd", None)

        if cmd is None or cmd == "":
            return self._cmd_summary(project_root)
        elif cmd == "show":
            return self._cmd_show(project_root, args)
        elif cmd == "validate":
            return self._cmd_validate(project_root, args)
        elif cmd == "list":
            return self._cmd_list(project_root)
        else:
            return self._cmd_summary(project_root)

    def _cmd_summary(self, project_root: Path) -> int:
        """Show configuration summary."""
        log.banner("Project Configuration")

        config = ProjectConfig.load(project_root)
 
        # Project info
        if config.info:
            print(f"\n{log.Colors.BOLD}Project:{log.Colors.RESET}")
            print(f"  Name: {config.info.name}")
            print(f"  Version: {config.info.version}")
            if config.info.description:
                print(f"  Description: {config.info.description}")

        # Feature flags
        if config.features:
            print(f"\n{log.Colors.BOLD}Features:{log.Colors.RESET}")
            features = []
            for feat in ["firmware", "ip", "constraints"]:
                if config.is_enabled(feat):
                    features.append(feat)
            print(f"  Enabled: {', '.join(features) if features else 'none'}")

        # Sources info
        print(f"\n{log.Colors.BOLD}Sources:{log.Colors.RESET}")
        # Note: Top module info removed - now per-testbench
        testbenches = config.list_testbenches()
        print(f"  Testbenches: {len(testbenches)}")
        rtl_modules = config.list_rtl_modules()
        print(f"  RTL modules: {len(rtl_modules)}")
        ips = config.list_ips()
        print(f"  IPs: {len(ips)}")
        firmware = config.list_firmware()
        print(f"  Firmware: {len(firmware)}")

        # Defaults
        if config.defaults:
            print(f"\n{log.Colors.BOLD}Defaults:{log.Colors.RESET}")
            print(f"  Simulator: {config.defaults.simulator}")
            print(f"  Synthesizer: {config.defaults.synthesizer}")
            print(f"  Linter: {config.defaults.linter}")

        print()
        return 0

    def _cmd_show(self, project_root: Path, args) -> int:
        """Show configuration details."""
        config_dir = project_root / ".aly"

        if args.section:
            # Show specific section
            section_file = config_dir / f"{args.section}.yaml"
            if not section_file.exists():
                self.die(f"Configuration section not found: {args.section}")

            with open(section_file) as f:
                data = yaml.safe_load(f) or {}

            if args.json:
                print(json.dumps(data, indent=2, default=str))
            else:
                log.banner(f"Configuration: {args.section}")
                print(yaml.dump(data, default_flow_style=False, sort_keys=False))
        else:
            # Show all configuration - validate it loads
            try:
                ProjectConfig.load(project_root)
            except ConfigurationError as e:
                self.die(str(e))

            if args.json:
                # Collect all raw data
                all_config = {}
                for section in ProjectConfig.CONFIG_FILES.keys():
                    section_file = config_dir / f"{section}.yaml"
                    if section_file.exists():
                        with open(section_file) as f:
                            all_config[section] = yaml.safe_load(f) or {}
                print(json.dumps(all_config, indent=2, default=str))
            else:
                log.banner("Full Configuration")
                for section, filename in ProjectConfig.CONFIG_FILES.items():
                    section_file = config_dir / filename
                    if section_file.exists():
                        print(f"\n{log.Colors.BOLD}[{section}]{log.Colors.RESET}")
                        with open(section_file) as f:
                            data = yaml.safe_load(f) or {}
                        print(
                            yaml.dump(data, default_flow_style=False, sort_keys=False)
                        )

        return 0

    def _cmd_validate(self, project_root: Path, args) -> int:
        """Validate configuration."""
        log.banner("Validating Configuration")

        config_dir = project_root / ".aly"
        errors = []
        warnings = []

        # Check config directory exists
        if not config_dir.exists():
            errors.append("Configuration directory .aly/ not found")
            log.err("Configuration directory .aly/ not found")
            return 1

        # Check main config
        main_config = config_dir / "config.yaml"
        if not main_config.exists():
            errors.append("Main configuration file .aly/config.yaml not found")

        # Try to load configuration
        try:
            config = ProjectConfig.load(project_root)
            log.success("Configuration loaded successfully")
        except:
            log.die(f"Failed to load configuration")
            return 1

        # Validate sources
        testbenches = config.list_testbenches()
        if not testbenches:
            warnings.append("No testbenches found")
        else:
            log.inf(f"Found {len(testbenches)} testbenches")

        rtl_blocks = config.list_rtl_modules()
        if not rtl_blocks:
            warnings.append("No RTL blocks found")
        else:
            log.inf(f"Found {len(rtl_blocks)} RTL blocks")

        # Check for required config files based on features
        if config.is_enabled("sim"):
            sim_file = config_dir / "sim.yaml"
            if not sim_file.exists():
                warnings.append("Simulation enabled but sim.yaml not found")

        if config.is_enabled("synth"):
            synth_file = config_dir / "synth.yaml"
            if not synth_file.exists():
                warnings.append("Synthesis enabled but synth.yaml not found")

        # Report results
        print()
        if errors:
            log.err(f"Errors: {len(errors)}")
            for e in errors:
                log.err(f"  • {e}")

        if warnings:
            log.wrn(f"Warnings: {len(warnings)}")
            for w in warnings:
                log.wrn(f"  • {w}")

        if not errors and not warnings:
            log.success("Configuration is valid")
            return 0
        elif errors:
            return 1
        elif args.strict:
            return 1
        else:
            return 0

    def _cmd_list(self, project_root: Path) -> int:
        """List configuration files."""
        config_dir = project_root / ".aly"

        if not config_dir.exists():
            self.die("Configuration directory .aly/ not found")

        log.banner("Configuration Files")

        for section, filename in sorted(ProjectConfig.CONFIG_FILES.items()):
            section_file = config_dir / filename
            if section_file.exists():
                size = section_file.stat().st_size
                print(
                    f"  {log.Colors.GREEN}✓{log.Colors.RESET} {filename:20} ({size:,} bytes)"
                )
            else:
                print(
                    f"  {log.Colors.YELLOW}○{log.Colors.RESET} {filename:20} (not found)"
                )

        return 0

    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists in PATH."""
        import shutil

        return shutil.which(cmd) is not None
