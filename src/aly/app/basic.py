# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Basic utility commands for ALY."""

import shutil
import sys
from pathlib import Path

from aly import __version__, log
from aly.commands import AlyCommand
from aly.util import find_aly_root, find_tool
from aly.config import ProjectConfig


class Info(AlyCommand):
    """Display ALY configuration and toolchain status."""

    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            "info", help="display configuration and toolchain status"
        )
        parser.add_argument(
            "--project",
            "-p",
            action="store_true",
            help="show detailed project configuration (tests, IPs, firmware)",
        )
        parser.add_argument(
            "--tools",
            action="store_true",
            help="show only toolchain status",
        )
        return parser

    def run(self, args, unknown_args):
        log.banner("ALY Configuration")

        # ALY Tool Information
        print(f"\n{log.Colors.BOLD}ALY Tool:{log.Colors.RESET}")
        print(f"  Version: {__version__}")
        print(f"  Python: {sys.version.split()[0]}")

        # Project Information
        project_root = find_aly_root()
        if not project_root:
            print(f"\n{log.Colors.BOLD}Project:{log.Colors.RESET}")
            log.wrn("Not in an ALY project (no .aly directory found)")
            print()
            return 0

        log.inf(f"Project Root: {project_root}")
        build_dir = project_root / "build"
        log.inf(f"Build Directory: {build_dir}")

        # Show project details if requested
        if args.project:
            return self._show_project_details(project_root)

        # Show only tools if requested
        if args.tools:
            return self._show_tools_only(project_root)

        # Default: show project summary with tools
        # Load project configuration to detect required tools
        required_tools = self._detect_required_tools(project_root)

        # Toolchain Status
        print(f"\n{log.Colors.BOLD}Toolchains:{log.Colors.RESET}")

        # Check each required toolchain
        if "firmware" in required_tools:
            self._check_firmware_toolchain(required_tools["firmware"])

        if "simulator" in required_tools:
            self._check_simulators(required_tools["simulator"])

        if "synthesis" in required_tools:
            self._check_synthesis_tools(required_tools["synthesis"])

        if "formal" in required_tools:
            self._check_formal_tools(required_tools["formal"])

        print()
        return 0

    def _show_tools_only(self, project_root: Path) -> int:
        """Show comprehensive toolchain status (all known tools)."""
        print(f"\n{log.Colors.BOLD}All Available Toolchains:{log.Colors.RESET}")

        # Check all firmware toolchains
        print(f"\n  {log.Colors.BOLD}Firmware:{log.Colors.RESET}")
        for tc in ["riscv64", "riscv32", "arm"]:
            self._check_firmware_toolchain(tc)

        # Check all simulators
        print(f"\n  {log.Colors.BOLD}Simulators:{log.Colors.RESET}")
        self._check_simulators(["xsim", "questa", "verilator", "icarus", "vcs"])

        # Check all synthesis tools
        print(f"\n  {log.Colors.BOLD}Synthesis:{log.Colors.RESET}")
        self._check_synthesis_tools(["vivado", "yosys", "quartus"])

        # Check formal tools
        print(f"\n  {log.Colors.BOLD}Formal:{log.Colors.RESET}")
        self._check_formal_tools(["symbiyosys", "jaspergold"])

        # Check waveform viewers
        print(f"\n  {log.Colors.BOLD}Waveform Viewers:{log.Colors.RESET}")
        self._check_waveform_viewers(["gtkwave"])

        print()
        return 0

    def _show_project_details(self, project_root: Path) -> int:
        """Show detailed project configuration."""
        try:
            config = ProjectConfig.load(project_root)
        except Exception as e:
            log.err(f"Failed to load configuration: {e}")
            return 1

        # Project Info
        print(f"\n{log.Colors.BOLD}Project:{log.Colors.RESET}")
        print(f"  Name:     {config.project.name}")
        print(f"  Version:  {config.project.version}")
        print(f"  Language: {config.project.language}")
        # Top module removed - now per-testbench

        # Feature Flags (show the actual configurable features)
        print(f"\n{log.Colors.BOLD}Feature Flags:{log.Colors.RESET}")
        features = config.features
        for feat in ["firmware", "ip", "constraints"]:
            enabled = getattr(features, feat, False) if features else False
            status = (
                f"{log.Colors.GREEN}✓{log.Colors.RESET}"
                if enabled
                else f"{log.Colors.RED}✗{log.Colors.RESET}"
            )
            print(f"  {feat}: {status}")

        # Capabilities (based on config file existence)
        print(f"\n{log.Colors.BOLD}Capabilities:{log.Colors.RESET}")
        aly_dir = project_root / ".aly"
        capabilities = {
            "simulation": (aly_dir / "sim.yaml").exists()
            or (aly_dir / "toolchains.yaml").exists(),
            "synthesis": (aly_dir / "synth.yaml").exists(),
            "lint": (aly_dir / "lint.yaml").exists(),
            "formal": (aly_dir / "formal.yaml").exists(),
            "ci": (aly_dir / "ci.yaml").exists(),
        }
        for cap, available in capabilities.items():
            status = (
                f"{log.Colors.GREEN}✓{log.Colors.RESET}"
                if available
                else f"{log.Colors.DIM}-{log.Colors.RESET}"
            )
            print(f"  {cap}: {status}")

        # Components
        testbenches = config.list_testbenches()
        rtl_blocks = config.list_rtl_blocks()
        ips = config.list_ips()
        firmware_builds = config.list_firmware()

        print(f"\n{log.Colors.BOLD}Components:{log.Colors.RESET}")
        print(f"  RTL Blocks: {len(rtl_blocks)}")
        print(f"  IPs: {len(ips)}")
        print(f"  Testbenches: {len(testbenches)}")
        print(f"  Firmware: {len(firmware_builds)}")

        # Testbenches
        print(f"\n{log.Colors.BOLD}Testbenches ({len(testbenches)}):{log.Colors.RESET}")
        if all_tests:
            for name, test in sorted(all_tests.items()):
                top = test.top or name
                tags = f" [{', '.join(test.tags)}]" if test.tags else ""
                fw = f" [fw: {test.firmware.build}]" if test.firmware else ""
                print(f"  {name} (top: {top}){tags}{fw}")
        else:
            print("  (none defined)")

        # IPs
        ips = config.list_ips()
        print(f"\n{log.Colors.BOLD}IP Blocks ({len(ips)}):{log.Colors.RESET}")
        if ips:
            for ip_name in ips:
                ip = config.get_ip(ip_name)
                version = ip.version if ip else "-"
                print(f"  {ip_name} (v{version})")
        else:
            print("  (none)")

        # Firmware builds
        if config.is_enabled("firmware"):
            firmware_builds = config.list_firmware()
            print(
                f"\n{log.Colors.BOLD}Firmware Builds ({len(firmware_builds)}):{log.Colors.RESET}"
            )
            if firmware_builds:
                for name in sorted(firmware_builds):
                    fw = config.get_firmware(name)
                    sources = len(fw.files) if fw else 0
                    print(f"  {name} ({sources} sources)")
            else:
                print("  (none defined)")

        # Defaults
        print(f"\n{log.Colors.BOLD}Defaults:{log.Colors.RESET}")
        if config.defaults:
            print(f"  Simulator:   {config.defaults.simulator or '-'}")
            print(f"  Synthesizer: {config.defaults.synthesizer or '-'}")
            print(f"  Linter:      {config.defaults.linter or '-'}")
            print(f"  Toolchain:   {config.defaults.toolchain or '-'}")

        print()
        return 0

    def _detect_required_tools(self, project_root: Path) -> dict:
        """Detect required tools from project configuration."""
        required = {}

        try:
            config = ProjectConfig.load(project_root)

            # Detect firmware toolchain
            if config.is_enabled("firmware"):
                required["firmware"] = config.firmware.default_toolchain

            # Detect simulators (from defaults)
            if config.defaults:
                if config.defaults.simulator:
                    required["simulator"] = [config.defaults.simulator]
                if config.defaults.synthesizer:
                    required["synthesis"] = [config.defaults.synthesizer]
                if config.defaults.formal_tool:
                    required["formal"] = [config.defaults.formal_tool]

        except Exception:
            # If config parsing fails, fall back to common tools
            pass

        # If no config or parsing failed, provide defaults
        if not required:
            required = {
                "firmware": "riscv64",
                "simulator": ["xsim", "questa", "verilator"],
                "synthesis": ["vivado", "yosys"],
            }

        return required

    def _check_firmware_toolchain(self, toolchain: str):
        """Check firmware toolchain availability."""
        toolchain_map = {
            "riscv64": {
                "name": "RISC-V 64-bit",
                "prefix": "riscv64-unknown-elf-",
                "tools": ["gcc", "as", "ld", "objcopy", "objdump"],
            },
            "riscv32": {
                "name": "RISC-V 32-bit",
                "prefix": "riscv32-unknown-elf-",
                "tools": ["gcc", "as", "ld", "objcopy", "objdump"],
            },
            "arm": {
                "name": "ARM",
                "prefix": "arm-none-eabi-",
                "tools": ["gcc", "as", "ld", "objcopy", "objdump"],
            },
        }

        if toolchain not in toolchain_map:
            return

        tc = toolchain_map[toolchain]
        tools = [tc["prefix"] + tool for tool in tc["tools"]]
        all_found = all(find_tool(t) for t in tools)

        status = (
            f"{log.Colors.GREEN}✓ Ready{log.Colors.RESET}"
            if all_found
            else f"{log.Colors.RED}✗ Not Found{log.Colors.RESET}"
        )
        print(f"  {tc['name']}: {status}")

    def _check_simulators(self, simulators: list):
        """Check simulator availability."""
        simulator_tools = {
            "xsim": {
                "name": "Vivado XSim",
                "tools": ["xvlog.bat", "xelab.bat", "xsim.bat"]
                if sys.platform == "win32"
                else ["xvlog", "xelab", "xsim"],
            },
            "questa": {
                "name": "Questa/ModelSim",
                "tools": ["vlog", "vlib", "vsim"],
            },
            "verilator": {
                "name": "Verilator",
                "tools": ["verilator"],
            },
            "vcs": {
                "name": "Synopsys VCS",
                "tools": ["vcs"],
            },
            "icarus": {
                "name": "Icarus Verilog",
                "tools": ["iverilog", "vvp"],
            },
        }

        if isinstance(simulators, str):
            simulators = [simulators]

        for sim in simulators:
            if sim not in simulator_tools:
                continue

            sim_info = simulator_tools[sim]
            all_found = all(find_tool(t) for t in sim_info["tools"])

            status = (
                f"{log.Colors.GREEN}✓ Ready{log.Colors.RESET}"
                if all_found
                else f"{log.Colors.RED}✗ Not Found{log.Colors.RESET}"
            )
            print(f"  {sim_info['name']}: {status}")

    def _check_synthesis_tools(self, tools: list):
        """Check synthesis tool availability."""
        synth_tools = {
            "vivado": {
                "name": "Xilinx Vivado",
                "tools": ["vivado.bat"] if sys.platform == "win32" else ["vivado"],
            },
            "yosys": {
                "name": "Yosys",
                "tools": ["yosys"],
            },
            "quartus": {
                "name": "Intel Quartus",
                "tools": ["quartus_sh"],
            },
        }

        if isinstance(tools, str):
            tools = [tools]

        for tool in tools:
            if tool not in synth_tools:
                continue

            tool_info = synth_tools[tool]
            all_found = all(find_tool(t) for t in tool_info["tools"])

            status = (
                f"{log.Colors.GREEN}✓ Ready{log.Colors.RESET}"
                if all_found
                else f"{log.Colors.RED}✗ Not Found{log.Colors.RESET}"
            )
            print(f"  {tool_info['name']}: {status}")

    def _check_formal_tools(self, tools: list):
        """Check formal verification tool availability."""
        formal_tools = {
            "symbiyosys": {
                "name": "SymbiYosys",
                "tools": ["sby"],
            },
            "jaspergold": {
                "name": "JasperGold",
                "tools": ["jg"],
            },
        }

        if isinstance(tools, str):
            tools = [tools]

        for tool in tools:
            if tool not in formal_tools:
                continue

            tool_info = formal_tools[tool]
            all_found = all(find_tool(t) for t in tool_info["tools"])

            status = (
                f"{log.Colors.GREEN}✓ Ready{log.Colors.RESET}"
                if all_found
                else f"{log.Colors.RED}✗ Not Found{log.Colors.RESET}"
            )
            print(f"  {tool_info['name']}: {status}")

    def _check_waveform_viewers(self, tools: list):
        """Check waveform viewer availability."""
        viewer_tools = {
            "gtkwave": {
                "name": "GTKWave",
                "tools": ["gtkwave"],
            },
        }

        if isinstance(tools, str):
            tools = [tools]

        for tool in tools:
            if tool not in viewer_tools:
                continue

            tool_info = viewer_tools[tool]
            all_found = all(find_tool(t) for t in tool_info["tools"])

            status = (
                f"{log.Colors.GREEN}✓ Ready{log.Colors.RESET}"
                if all_found
                else f"{log.Colors.RED}✗ Not Found{log.Colors.RESET}"
            )
            print(f"  {tool_info['name']}: {status}")


class Clean(AlyCommand):
    """Remove build artifacts."""

    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser("clean", help="remove build artifacts")
        return parser

    def run(self, args, unknown_args):
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        build_dir = project_root / "build"

        if build_dir.exists():
            log.inf(f"Removing {build_dir}")
            shutil.rmtree(build_dir)
            log.success("Build directory cleaned")
        else:
            log.inf("Build directory doesn't exist, nothing to clean")

        return 0


class Refresh(AlyCommand):
    """Force re-discovery of all project components."""

    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            "refresh",
            help="force re-discovery of all project components (manifests, RTL, testbenches, firmware, packages)"
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="show detailed discovery information"
        )
        return parser

    def run(self, args, unknown_args):
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        try:
            log.inf("Refreshing project components...")
            config = ProjectConfig.load(project_root)

            # Force refresh
            config.refresh()

            # Get component summary
            after_summary = config.summary()

            log.success("Component discovery refreshed")

            # Show summary
            print(f"\n{log.Colors.BOLD}Discovered Components:{log.Colors.RESET}")
            for component_type, count in after_summary.items():
                if count > 0:
                    print(f"  {component_type}: {count}")

            if args.verbose:
                # Show detailed breakdown
                print(f"\n{log.Colors.BOLD}RTL Modules:{log.Colors.RESET}")
                for name in sorted(config.list_rtl_modules()):
                    print(f"  - {name}")

                print(f"\n{log.Colors.BOLD}Packages:{log.Colors.RESET}")
                for name in sorted(config.list_packages()):
                    print(f"  - {name}")

                print(f"\n{log.Colors.BOLD}Testbenches:{log.Colors.RESET}")
                for name in sorted(config.list_testbenches()):
                    print(f"  - {name}")

                print(f"\n{log.Colors.BOLD}Firmware Builds:{log.Colors.RESET}")
                for name in sorted(config.list_firmware()):
                    print(f"  - {name}")

            print()
            return 0

        except Exception as e:
            self.die(f"Failed to refresh: {e}")


class Version(AlyCommand):
    """Show ALY version."""

    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser("version", help="show ALY version")
        return parser

    def run(self, args, unknown_args):
        print(f"ALY version {__version__}")
        print(f"Python {sys.version}")
        return 0
