# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Firmware command - builds firmware for processor-based SoCs.

This command provides a CLI interface to the firmware backend system.
The actual build logic is in the FirmwareBackend classes.

Supports multiple toolchains:
- RISC-V (riscv64-unknown-elf, riscv32-unknown-elf)
- ARM (arm-none-eabi)
- Custom toolchains via workflow configuration

Outputs:
- ELF executable
- Binary file
- Memory initialization file (.mem) for simulation
- Disassembly listing
"""

from pathlib import Path
from typing import Dict, Any, Optional, List

from aly import log
from aly.commands import AlyCommand
from aly.util import find_aly_root
from aly.fw_gcc import GccFirmwareBackend
from aly.backends import FirmwareBackend, FirmwareResult


# Registry of firmware backends by toolchain type
FIRMWARE_BACKENDS: Dict[str, type] = {
    "riscv64": GccFirmwareBackend,
    "riscv32": GccFirmwareBackend,
    "arm": GccFirmwareBackend,
    "custom": GccFirmwareBackend,
}


def get_firmware_backend(
    toolchain_name: str,
    toolchain_config: Dict[str, Any],
    project_root: Path,
) -> Optional[FirmwareBackend]:
    """Get firmware backend for a toolchain.

    Args:
        toolchain_name: Name of the toolchain (riscv64, arm, etc.)
        toolchain_config: Toolchain configuration dict
        project_root: Project root directory

    Returns:
        FirmwareBackend instance or None if toolchain not supported
    """
    backend_class = FIRMWARE_BACKENDS.get(toolchain_name, GccFirmwareBackend)
    return backend_class(toolchain_config, project_root)


def build_firmware(
    build_config: Any,
    toolchain_config: Dict[str, Any],
    project_root: Path,
    output_dir: Path,
    mem_formats: Optional[List[Dict[str, Any]]] = None,
    toolchain_name: str = "riscv64",
) -> FirmwareResult:
    """Build firmware using the appropriate backend.

    This is the main API for programmatic firmware building.
    Used by the simulate command for testbench firmware dependencies.

    Args:
        build_config: FirmwareBuildConfig instance
        toolchain_config: Toolchain configuration dict
        project_root: Project root directory
        output_dir: Output directory for build artifacts
        mem_formats: List of memory format configurations
        toolchain_name: Name of the toolchain

    Returns:
        FirmwareResult with build status and file paths
    """
    backend = get_firmware_backend(toolchain_name, toolchain_config, project_root)
    if backend is None:
        return FirmwareResult(
            success=False,
            duration=0,
            build_name=build_config.name,
            stderr=f"No backend for toolchain: {toolchain_name}",
        )

    if not backend.check_toolchain():
        prefix = toolchain_config.get("prefix", f"{toolchain_name}-")
        return FirmwareResult(
            success=False,
            duration=0,
            build_name=build_config.name,
            stderr=f"Toolchain not found: {prefix}gcc",
        )

    return backend.build(build_config, output_dir, mem_formats)


class Firmware(AlyCommand):
    """Build firmware for processor-based SoCs."""

    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            "firmware",
            help="build firmware (.mem files for simulation)",
            description="Build firmware from C/ASM sources. Supports RISC-V, ARM, and custom toolchains.",
        )
        parser.add_argument(
            "build",
            nargs="?",
            help="firmware build name from project config (default: all)",
        )
        parser.add_argument(
            "-o", "--output", help="output directory (default: build/firmware)"
        )
        parser.add_argument(
            "--toolchain",
            help="override toolchain (e.g., riscv64, riscv32, arm)",
        )
        parser.add_argument(
            "--no-mem",
            action="store_true",
            help="skip .mem file generation",
        )
        parser.add_argument(
            "--mem-format",
            choices=["hex", "mem", "coe", "verilog", "bin"],
            default="mem",
            help="memory file format (default: mem)",
        )
        parser.add_argument(
            "--word-width",
            type=int,
            choices=[8, 16, 32, 64],
            default=32,
            help="memory word width in bits (default: 32)",
        )
        parser.add_argument(
            "--byte-order",
            choices=["little", "big"],
            default="little",
            help="byte order (default: little)",
        )

        # List mode
        parser.add_argument(
            "--list",
            action="store_true",
            help="list available firmware builds and exit",
        )
        return parser

    def run(self, args, unknown_args):
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        # Load project config
        try:
            from aly.config import ProjectConfig

            config = ProjectConfig.load(project_root)
        except Exception as e:
            self.die(f"Failed to load config: {e}")

        # List mode
        if args.list:
            return self._list_builds(config)

        # Check if firmware is enabled
        if not config.is_enabled("firmware"):
            log.inf("Firmware is not enabled for this project.")
            log.inf("Set 'firmware: true' in .aly/config.yaml features if needed.")
            return 0

        # Get toolchain
        toolchain_name = args.toolchain or config.defaults.toolchain
        if toolchain_name == "none":
            log.inf("No firmware toolchain configured (pure RTL project).")
            return 0

        # Get toolchain config
        tc = config.get_toolchain(toolchain_name)
        if tc is None:
            self.die(f"Toolchain not found: {toolchain_name}")

        # Convert toolchain config to dict for backend
        tc_config = {
            "prefix": tc.prefix or f"{toolchain_name}-",
            "march": tc.march,
            "mabi": tc.mabi,
            "cpu": tc.cpu,
        }

        # Get backend and check toolchain
        backend = get_firmware_backend(toolchain_name, tc_config, project_root)
        if backend is None:
            self.die(f"No backend for toolchain: {toolchain_name}")

        if not backend.check_toolchain():
            self.die(f"Toolchain not found: {tc_config['prefix']}gcc")

        # Setup output directory
        if args.output:
            output_dir = Path(args.output)
        else:
            output_dir = project_root / "build" / "fw"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get builds to process
        if args.build:
            build = config.get_firmware(args.build)
            if build is None:
                self.die(f"Firmware build not found: {args.build}")
            builds = [build]
        else:
            firmware_names = config.list_firmware()
            builds = [config.get_firmware(name) for name in firmware_names]

        if not builds:
            log.wrn("No firmware builds defined in project config.")
            log.inf("Add firmware manifests under fw/<name>/manifest.yaml and define toolchains in .aly/toolchains.yaml")
            return 0

        log.banner(f"Building Firmware ({len(builds)} builds)")
        log.inf(f"Default Toolchain: {tc_config['prefix']}")

        # Prepare memory format config
        mem_formats = None
        if not args.no_mem:
            mem_formats = [
                {
                    "format": args.mem_format,
                    "word_width": args.word_width,
                    "byte_order": args.byte_order,
                }
            ]

        success_count = 0
        for build in builds:
            try:
                # Check for per-build toolchain override
                build_tc_config = tc_config
                build_tc_name = toolchain_name

                if build.toolchain:
                    build_tc = config.get_toolchain(build.toolchain)
                    if build_tc:
                        build_tc_name = build.toolchain
                        build_tc_config = {
                            "prefix": build_tc.prefix or f"{build.toolchain}-",
                            "march": build_tc.march,
                            "mabi": build_tc.mabi,
                            "cpu": build_tc.cpu,
                        }

                        # Verify toolchain is available
                        build_backend = get_firmware_backend(
                            build_tc_name, build_tc_config, project_root
                        )
                        if build_backend and not build_backend.check_toolchain():
                            log.err(
                                f"Toolchain not found for {build.name}: {build_tc_config['prefix']}gcc"
                            )
                            continue

                # Build firmware
                result = build_firmware(
                    build,
                    build_tc_config,
                    project_root,
                    output_dir,
                    mem_formats,
                    build_tc_name,
                )

                if result.success:
                    success_count += 1
                else:
                    log.err(f"Failed to build {build.name}: {result.stderr}")

            except Exception as e:
                log.err(f"Failed to build {build.name}: {e}")

        # Summary
        print()
        log.inf(f"Built {success_count}/{len(builds)} firmware builds")
        log.inf(f"Output: {output_dir}")

        return 0 if success_count == len(builds) else 1

    def _list_builds(self, config):
        """List available firmware builds."""
        # Check if firmware is enabled
        if not config.is_enabled("firmware"):
            log.inf("Firmware is not enabled for this project.")
            log.inf("Set 'firmware: true' in .aly/config.yaml features if needed.")
            return 0

        firmware_names = config.list_firmware()
        builds = {name: config.get_firmware(name) for name in firmware_names}
        toolchains = {name: config.get_toolchain(name) for name in ["riscv64", "riscv32", "arm", "custom"] if config.get_toolchain(name)}
        default_tc = config.defaults.toolchain

        log.banner(f"Firmware Builds ({len(builds)})")

        # Show toolchain info
        print(f"\n{log.Colors.BOLD}Toolchains:{log.Colors.RESET}")
        print(f"  Default: {default_tc}")
        for name, tc in toolchains.items():
            if tc:
                prefix = tc.prefix or f"{name}-"
                arch = tc.march or tc.cpu or "-"
                print(f"  {name}: prefix={prefix}, arch={arch}")

        # Show builds
        if not builds:
            print(f"\n{log.Colors.BOLD}Builds:{log.Colors.RESET}")
            log.wrn("No firmware builds defined.")
            log.inf("Add firmware manifests under fw/<name>/manifest.yaml and define toolchains in .aly/toolchains.yaml")
            return 0

        print(f"\n{log.Colors.BOLD}Builds:{log.Colors.RESET}")
        for name, build in sorted(builds.items()):
            print(f"\n  {log.Colors.BOLD}{name}{log.Colors.RESET}")
            print(f"    Sources:  {len(build.sources)} files")
            if build.linker_script:
                print(f"    Linker:   {build.linker_script}")
            if build.toolchain:
                print(f"    Toolchain: {build.toolchain} (override)")
            if build.includes:
                print(f"    Includes: {', '.join(build.includes)}")

        print()
        return 0
