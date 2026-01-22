# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Program command - FPGA bitstream programming.

This module provides FPGA programming capabilities using various backends:
- Vivado Hardware Server (Xilinx/AMD FPGAs)
- openFPGALoader (open-source, multi-vendor)
- Quartus Programmer (Intel/Altera FPGAs)

Architecture:
    The Program command supports multiple programming backends, each
    implementing the ProgrammerBackend interface. The command:
    1. Discovers available programmers and connected devices
    2. Locates the bitstream file to program
    3. Invokes the appropriate backend to program the FPGA

    Bitstreams are located from synthesis output directories based on
    the --target option, or can be specified directly with --bitstream.

    Integrates with ProjectConfig for FPGA target configuration.

Usage:
    aly program --target arty_a7           # Program from synthesis output
    aly program --bitstream path/to.bit    # Program specific file
    aly program --list                     # List connected devices
    aly program --flash                    # Program to flash (persistent)
    aly program --verify                   # Verify after programming

Supported Boards:
    The command supports any board with a JTAG interface. Common boards:
    - Xilinx: Arty, Basys3, Nexys, Zybo, ZCU series
    - Intel: DE10-Nano, DE2, Cyclone boards
    - Lattice: iCEStick, iCE40-HX8K, ECP5 boards
"""

import argparse
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from aly import log
from aly.commands import AlyCommand
from aly.util import find_aly_root, find_tool
from aly.config import ProjectConfig


@dataclass
class Device:
    """Represents a connected FPGA device."""

    name: str
    part: str
    serial: Optional[str] = None
    index: int = 0
    backend: str = ""


@dataclass
class ProgramResult:
    """Result of a programming operation."""

    success: bool
    duration: float
    device: Optional[Device] = None
    message: str = ""


class ProgrammerBackend:
    """Base class for programmer backends."""

    name: str = "base"

    def __init__(self, config: Dict[str, Any], project_root: Path):
        self.config = config
        self.project_root = project_root

    def check_available(self) -> bool:
        """Check if the programmer is available."""
        raise NotImplementedError

    def list_devices(self) -> List[Device]:
        """List connected devices."""
        raise NotImplementedError

    def program(
        self,
        bitstream: Path,
        device: Optional[Device] = None,
        flash: bool = False,
        verify: bool = False,
    ) -> ProgramResult:
        """Program the FPGA."""
        raise NotImplementedError


class VivadoProgrammer(ProgrammerBackend):
    """Vivado Hardware Server programmer backend.

    Uses Vivado's hw_server and vivado batch mode for programming
    Xilinx/AMD FPGAs. Supports JTAG programming and SPI flash.
    """

    name = "vivado"

    def check_available(self) -> bool:
        """Check if Vivado is available."""
        # Check for vivado or vivado_lab
        return find_tool("vivado") is not None or find_tool("vivado_lab") is not None

    def _get_vivado_cmd(self) -> str:
        """Get the Vivado command to use."""
        if find_tool("vivado_lab"):
            return "vivado_lab"
        return "vivado"

    def list_devices(self) -> List[Device]:
        """List connected devices using Vivado."""
        devices = []

        tcl_script = """
open_hw_manager
connect_hw_server -allow_non_jtag
foreach target [get_hw_targets] {
    open_hw_target $target
    foreach device [get_hw_devices] {
        set part [get_property PART $device]
        puts "DEVICE:$device:$part"
    }
    close_hw_target
}
disconnect_hw_server
close_hw_manager
exit
"""
        try:
            result = subprocess.run(
                [self._get_vivado_cmd(), "-mode", "batch", "-source", "/dev/stdin"],
                input=tcl_script,
                capture_output=True,
                text=True,
                timeout=30,
            )

            for line in result.stdout.splitlines():
                if line.startswith("DEVICE:"):
                    parts = line.split(":")
                    if len(parts) >= 3:
                        devices.append(
                            Device(
                                name=parts[1],
                                part=parts[2],
                                backend=self.name,
                            )
                        )
        except Exception as e:
            log.dbg(f"Failed to list Vivado devices: {e}")

        return devices

    def program(
        self,
        bitstream: Path,
        device: Optional[Device] = None,
        flash: bool = False,
        verify: bool = False,
    ) -> ProgramResult:
        """Program using Vivado."""
        start_time = time.time()

        if flash:
            # Flash programming requires .mcs file and more complex flow
            tcl_script = f"""
open_hw_manager
connect_hw_server -allow_non_jtag
open_hw_target

set device [lindex [get_hw_devices] 0]
current_hw_device $device

# Create memory configuration device
create_hw_cfgmem -hw_device $device [lindex [get_cfgmem_parts {{s25fl128sxxxxxx0-spi-x1_x2_x4}}] 0]
set cfgmem [get_property PROGRAM.HW_CFGMEM $device]

set_property PROGRAM.FILES [list {{{bitstream}}}] $cfgmem
set_property PROGRAM.ADDRESS_RANGE {{use_file}} $cfgmem
set_property PROGRAM.BLANK_CHECK 0 $cfgmem
set_property PROGRAM.ERASE 1 $cfgmem
set_property PROGRAM.CFG_PROGRAM 1 $cfgmem
set_property PROGRAM.VERIFY {"1" if verify else "0"} $cfgmem

program_hw_cfgmem -hw_cfgmem $cfgmem

close_hw_target
disconnect_hw_server
close_hw_manager
exit
"""
        else:
            # SRAM programming (volatile)
            tcl_script = f"""
open_hw_manager
connect_hw_server -allow_non_jtag
open_hw_target

set device [lindex [get_hw_devices] 0]
current_hw_device $device

set_property PROGRAM.FILE {{{bitstream}}} $device
{"set_property PROGRAM.VERIFY 1 $device" if verify else ""}

program_hw_devices $device

close_hw_target
disconnect_hw_server
close_hw_manager
exit
"""

        try:
            # Write TCL script to temp file
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".tcl", delete=False
            ) as f:
                f.write(tcl_script)
                tcl_file = f.name

            result = subprocess.run(
                [self._get_vivado_cmd(), "-mode", "batch", "-source", tcl_file],
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Clean up
            Path(tcl_file).unlink()

            duration = time.time() - start_time
            success = result.returncode == 0

            if not success:
                log.err(result.stderr)

            return ProgramResult(
                success=success,
                duration=duration,
                message="Programming complete" if success else result.stderr,
            )

        except subprocess.TimeoutExpired:
            return ProgramResult(
                success=False,
                duration=time.time() - start_time,
                message="Programming timed out",
            )
        except Exception as e:
            return ProgramResult(
                success=False,
                duration=time.time() - start_time,
                message=str(e),
            )


class OpenFPGALoaderProgrammer(ProgrammerBackend):
    """openFPGALoader programmer backend.

    Open-source, multi-vendor FPGA programmer supporting:
    - Xilinx (Spartan, Artix, Kintex, Zynq)
    - Intel/Altera (Cyclone, MAX)
    - Lattice (iCE40, ECP5, MachXO)
    - Gowin
    - Efinix
    """

    name = "openfpgaloader"

    def check_available(self) -> bool:
        """Check if openFPGALoader is available."""
        return find_tool("openFPGALoader") is not None

    def list_devices(self) -> List[Device]:
        """List connected devices."""
        devices = []

        try:
            result = subprocess.run(
                ["openFPGALoader", "--detect"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Parse output for detected devices
            for line in result.stdout.splitlines():
                if "idcode" in line.lower() or "detected" in line.lower():
                    devices.append(
                        Device(
                            name=line.strip(),
                            part="detected",
                            backend=self.name,
                        )
                    )

        except Exception as e:
            log.dbg(f"Failed to detect devices: {e}")

        return devices

    def program(
        self,
        bitstream: Path,
        device: Optional[Device] = None,
        flash: bool = False,
        verify: bool = False,
    ) -> ProgramResult:
        """Program using openFPGALoader."""
        start_time = time.time()

        cmd = ["openFPGALoader"]

        if flash:
            cmd.append("-f")  # Write to flash

        if verify:
            cmd.append("--verify")

        cmd.append(str(bitstream))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            if not success:
                log.err(result.stderr)

            return ProgramResult(
                success=success,
                duration=duration,
                message="Programming complete" if success else result.stderr,
            )

        except subprocess.TimeoutExpired:
            return ProgramResult(
                success=False,
                duration=time.time() - start_time,
                message="Programming timed out",
            )
        except Exception as e:
            return ProgramResult(
                success=False,
                duration=time.time() - start_time,
                message=str(e),
            )


class QuartusProgrammer(ProgrammerBackend):
    """Quartus Programmer backend for Intel/Altera FPGAs."""

    name = "quartus"

    def check_available(self) -> bool:
        """Check if Quartus programmer is available."""
        return find_tool("quartus_pgm") is not None

    def list_devices(self) -> List[Device]:
        """List connected devices."""
        devices = []

        try:
            result = subprocess.run(
                ["quartus_pgm", "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Parse output
            for line in result.stdout.splitlines():
                if ")" in line and "(" in line:
                    devices.append(
                        Device(
                            name=line.strip(),
                            part="intel",
                            backend=self.name,
                        )
                    )

        except Exception as e:
            log.dbg(f"Failed to detect devices: {e}")

        return devices

    def program(
        self,
        bitstream: Path,
        device: Optional[Device] = None,
        flash: bool = False,
        verify: bool = False,
    ) -> ProgramResult:
        """Program using Quartus."""
        start_time = time.time()

        cmd = ["quartus_pgm", "-m", "jtag"]

        if verify:
            cmd.extend(["-o", f"pv;{bitstream}"])
        else:
            cmd.extend(["-o", f"p;{bitstream}"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            return ProgramResult(
                success=success,
                duration=duration,
                message="Programming complete" if success else result.stderr,
            )

        except Exception as e:
            return ProgramResult(
                success=False,
                duration=time.time() - start_time,
                message=str(e),
            )


# Available programmer backends
PROGRAMMER_BACKENDS = {
    "vivado": VivadoProgrammer,
    "openfpgaloader": OpenFPGALoaderProgrammer,
    "quartus": QuartusProgrammer,
}


class Program(AlyCommand):
    """Program FPGA with bitstream.

    This command programs an FPGA with a bitstream file. It supports
    multiple programming backends (Vivado, openFPGALoader, Quartus)
    and can program to either SRAM (volatile) or flash (persistent).

    The bitstream is located automatically from synthesis outputs
    when using --target, or can be specified directly with --bitstream.

    Examples:
        aly program --target arty_a7           # From synthesis output
        aly program --bitstream design.bit     # Specific file
        aly program --list                     # List connected devices
        aly program --target arty_a7 --flash   # Program to flash
        aly program --target arty_a7 --verify  # Verify after programming
    """

    @staticmethod
    def add_parser(parser_adder):
        """Add program command parser."""
        parser = parser_adder.add_parser(
            "program",
            help="program FPGA with bitstream",
            description="Program an FPGA with a bitstream file. Supports "
            "Vivado, openFPGALoader, and Quartus backends.",
        )
        parser.add_argument(
            "--list",
            "-l",
            action="store_true",
            help="list connected FPGA devices",
        )
        parser.add_argument(
            "--target",
            "-t",
            help="synthesis target (looks for bitstream in build/synth/<tool>/<target>/)",
        )
        parser.add_argument(
            "--bitstream",
            "-b",
            type=Path,
            help="path to bitstream file (.bit, .bin, .sof, etc.)",
        )
        parser.add_argument(
            "--tool",
            choices=list(PROGRAMMER_BACKENDS.keys()),
            help="programmer tool (auto-detected if not specified)",
        )
        parser.add_argument(
            "--flash",
            "-f",
            action="store_true",
            help="program to flash memory (persistent across power cycles)",
        )
        parser.add_argument(
            "--verify",
            "-v",
            action="store_true",
            help="verify after programming",
        )
        return parser

    def run(self, args, unknown_args):
        """Execute program command."""
        project_root = find_aly_root()

        # List devices mode
        if args.list:
            return self._list_devices()

        # Need either --target or --bitstream
        if not args.target and not args.bitstream:
            self.die("Specify --target or --bitstream")

        # Load config for FPGA target lookup
        config = None
        if project_root:
            try:
                config = ProjectConfig.load(project_root)
            except Exception:
                pass

        # Find bitstream
        if args.bitstream:
            bitstream = args.bitstream
            if not bitstream.exists():
                self.die(f"Bitstream not found: {bitstream}")
        else:
            # First check config for bitstream path
            bitstream = None
            if config and config.fpga:
                fpga_target = config.fpga.get_target(args.target)
                if fpga_target and fpga_target.bitstream:
                    bitstream = config.fpga.resolve_path(fpga_target.bitstream)
                    if not bitstream.exists():
                        bitstream = None

            # Fallback to directory search
            if not bitstream:
                bitstream = self._find_bitstream(project_root, args.target)

            if not bitstream:
                self.die(
                    f"No bitstream found for target '{args.target}'\n"
                    f"Run 'aly synth --target {args.target} --impl' first"
                )

        log.inf(f"Bitstream: {bitstream}")

        # Get programmer backend
        backend = self._get_backend(args.tool, bitstream)
        if not backend:
            self.die(
                "No programmer available.\n"
                "Install one of: Vivado, openFPGALoader, or Quartus"
            )

        log.banner(f"FPGA Programming ({backend.name})")
        log.inf(f"Bitstream: {bitstream.name}")
        log.inf(f"Flash: {'Yes' if args.flash else 'No (SRAM)'}")
        log.inf(f"Verify: {'Yes' if args.verify else 'No'}")

        # Program
        result = backend.program(
            bitstream=bitstream,
            flash=args.flash,
            verify=args.verify,
        )

        # Report results
        print()
        log.inf("=== Results ===")
        log.inf(f"Duration: {result.duration:.2f}s")

        if result.success:
            log.success("Programming PASSED")
            return 0
        else:
            log.err(f"Programming FAILED: {result.message}")
            return 1

    def _list_devices(self) -> int:
        """List connected FPGA devices."""
        log.banner("Connected FPGA Devices")

        all_devices = []

        for name, backend_class in PROGRAMMER_BACKENDS.items():
            backend = backend_class({}, Path.cwd())
            if backend.check_available():
                devices = backend.list_devices()
                all_devices.extend(devices)

        if not all_devices:
            log.inf("No devices detected")
            log.inf("Make sure:")
            log.inf("  - FPGA board is connected via USB")
            log.inf("  - JTAG/USB drivers are installed")
            log.inf("  - Board is powered on")
            return 0

        for i, device in enumerate(all_devices):
            print(f"  [{i}] {device.name}")
            print(f"      Part: {device.part}")
            print(f"      Backend: {device.backend}")
            print()

        return 0

    def _find_bitstream(
        self, project_root: Optional[Path], target: str
    ) -> Optional[Path]:
        """Find bitstream file for a target."""
        if not project_root:
            return None

        # Look in synthesis output directories
        synth_dir = project_root / "build" / "synth"

        if not synth_dir.exists():
            return None

        # Search for bitstream files
        patterns = ["*.bit", "*.bin", "*.sof", "*.svf", "*.jed"]

        for tool_dir in synth_dir.iterdir():
            if not tool_dir.is_dir():
                continue

            target_dir = tool_dir / target
            if not target_dir.exists():
                continue

            # Look in bitstream subdirectory first
            bitstream_dir = target_dir / "bitstream"
            search_dirs = [bitstream_dir, target_dir]

            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue

                for pattern in patterns:
                    files = list(search_dir.glob(pattern))
                    if files:
                        return files[0]

        return None

    def _get_backend(
        self, tool: Optional[str], bitstream: Path
    ) -> Optional[ProgrammerBackend]:
        """Get an appropriate programmer backend."""
        # If tool specified, use it
        if tool:
            backend_class = PROGRAMMER_BACKENDS.get(tool)
            if backend_class:
                backend = backend_class({}, Path.cwd())
                if backend.check_available():
                    return backend
            return None

        # Auto-detect based on file extension
        ext = bitstream.suffix.lower()

        # Xilinx/AMD files
        if ext in [".bit", ".bin", ".mcs"]:
            # Prefer Vivado for Xilinx files
            for name in ["vivado", "openfpgaloader"]:
                backend_class = PROGRAMMER_BACKENDS[name]
                backend = backend_class({}, Path.cwd())
                if backend.check_available():
                    return backend

        # Intel/Altera files
        elif ext in [".sof", ".pof"]:
            for name in ["quartus", "openfpgaloader"]:
                backend_class = PROGRAMMER_BACKENDS[name]
                backend = backend_class({}, Path.cwd())
                if backend.check_available():
                    return backend

        # Generic - try openfpgaloader first (multi-vendor)
        else:
            for name in ["openfpgaloader", "vivado", "quartus"]:
                backend_class = PROGRAMMER_BACKENDS[name]
                backend = backend_class({}, Path.cwd())
                if backend.check_available():
                    return backend

        return None
