# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Terminal command - UART serial terminal for hardware communication.

This module provides a built-in serial terminal for communicating with
FPGA boards over UART. It supports:
- Auto-detection of serial ports
- Configurable baud rate, parity, stop bits
- Session logging to file
- Line-based and character-based modes

Architecture:
    The Terminal command uses pyserial for cross-platform serial port
    access. It runs an interactive session that:
    1. Opens the specified serial port
    2. Spawns a reader thread for incoming data
    3. Handles keyboard input and sends to device
    4. Optionally logs all communication to a file

Usage:
    aly terminal                           # Auto-detect port
    aly terminal --port COM3               # Specific port (Windows)
    aly terminal --port /dev/ttyUSB0       # Specific port (Linux)
    aly terminal --baud 115200             # Custom baud rate
    aly terminal --log session.log         # Log to file

Dependencies:
    This command requires pyserial: pip install pyserial
"""

import argparse
import sys
import threading
import time
from pathlib import Path
from typing import Optional, List

from aly import log
from aly.commands import AlyCommand
from aly.util import find_aly_root


def _check_pyserial():
    """Check if pyserial is installed."""
    try:
        import serial
        import serial.tools.list_ports

        return True
    except ImportError:
        return False


def _list_serial_ports() -> List[dict]:
    """List available serial ports with descriptions."""
    try:
        import serial.tools.list_ports

        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append(
                {
                    "device": port.device,
                    "description": port.description,
                    "hwid": port.hwid,
                    "manufacturer": port.manufacturer,
                }
            )
        return ports
    except ImportError:
        return []


def _auto_detect_port() -> Optional[str]:
    """Auto-detect a likely FPGA/microcontroller serial port.

    Looks for common USB-UART chip identifiers:
    - FTDI chips (common on FPGA boards)
    - Silicon Labs CP210x
    - Prolific PL2303
    - CH340/CH341 (cheap Chinese chips)
    - Digilent boards
    - Xilinx/AMD boards
    """
    try:
        import serial.tools.list_ports

        # Priority keywords for FPGA boards
        priority_keywords = [
            "digilent",
            "xilinx",
            "arty",
            "basys",
            "nexys",
            "zybo",
            "pynq",
            "fpga",
        ]

        # Common USB-UART identifiers
        uart_keywords = [
            "ftdi",
            "ft232",
            "ft2232",
            "cp210",
            "pl2303",
            "ch340",
            "ch341",
            "usb serial",
            "usb-serial",
            "uart",
            "ttyusb",
            "ttyacm",
        ]

        ports = list(serial.tools.list_ports.comports())

        # First pass: look for FPGA-specific ports
        for port in ports:
            desc_lower = (port.description or "").lower()
            hwid_lower = (port.hwid or "").lower()
            mfr_lower = (port.manufacturer or "").lower()
            combined = f"{desc_lower} {hwid_lower} {mfr_lower}"

            for keyword in priority_keywords:
                if keyword in combined:
                    return port.device

        # Second pass: look for any USB-UART
        for port in ports:
            desc_lower = (port.description or "").lower()
            hwid_lower = (port.hwid or "").lower()
            mfr_lower = (port.manufacturer or "").lower()
            combined = f"{desc_lower} {hwid_lower} {mfr_lower}"

            for keyword in uart_keywords:
                if keyword in combined:
                    return port.device

        # Fallback: return first available port
        if ports:
            return ports[0].device

        return None

    except ImportError:
        return None


class SerialTerminal:
    """Interactive serial terminal session.

    Handles bidirectional communication with a serial device,
    displaying received data and sending keyboard input.

    Attributes:
        port: Serial port device path
        baudrate: Communication speed in bps
        bytesize: Data bits (5-8)
        parity: Parity checking (N/E/O/M/S)
        stopbits: Stop bits (1, 1.5, 2)
        log_file: Optional file to log session
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: float = 1,
        log_file: Optional[Path] = None,
    ):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.log_file = log_file

        self._serial = None
        self._running = False
        self._reader_thread = None
        self._log_handle = None

    def _reader(self):
        """Reader thread - displays incoming data."""
        while self._running:
            try:
                if self._serial and self._serial.in_waiting:
                    data = self._serial.read(self._serial.in_waiting)
                    if data:
                        # Decode and display
                        text = data.decode("utf-8", errors="replace")
                        sys.stdout.write(text)
                        sys.stdout.flush()

                        # Log if enabled
                        if self._log_handle:
                            self._log_handle.write(text)
                            self._log_handle.flush()
                else:
                    time.sleep(0.01)  # Small delay to prevent busy-waiting
            except Exception:
                if self._running:
                    time.sleep(0.1)

    def run(self):
        """Run the interactive terminal session.

        Press Ctrl+] to exit the terminal.
        """
        import serial

        # Open log file if specified
        if self.log_file:
            self._log_handle = open(self.log_file, "w", encoding="utf-8")
            log.inf(f"Logging to: {self.log_file}")

        # Open serial port
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=0.1,
                write_timeout=1,
            )
        except serial.SerialException as e:
            if self._log_handle:
                self._log_handle.close()
            raise RuntimeError(f"Failed to open {self.port}: {e}")

        log.inf(f"Connected to {self.port} at {self.baudrate} baud")
        log.inf("Press Ctrl+] to exit\n")

        # Start reader thread
        self._running = True
        self._reader_thread = threading.Thread(target=self._reader, daemon=True)
        self._reader_thread.start()

        # Main loop - handle keyboard input
        try:
            if sys.platform == "win32":
                self._windows_input_loop()
            else:
                self._unix_input_loop()
        finally:
            self._running = False
            if self._reader_thread:
                self._reader_thread.join(timeout=1)
            if self._serial:
                self._serial.close()
            if self._log_handle:
                self._log_handle.close()

        print("\nDisconnected.")

    def _windows_input_loop(self):
        """Input loop for Windows using msvcrt."""
        import msvcrt

        while self._running:
            if msvcrt.kbhit():
                ch = msvcrt.getch()

                # Ctrl+] (0x1D) to exit
                if ch == b"\x1d":
                    break

                # Send to serial
                try:
                    self._serial.write(ch)
                except Exception:
                    pass
            else:
                time.sleep(0.01)

    def _unix_input_loop(self):
        """Input loop for Unix using termios."""
        import termios
        import tty
        import select

        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)

        try:
            # Set raw mode
            tty.setraw(sys.stdin.fileno())

            while self._running:
                # Check for input with timeout
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)

                if rlist:
                    ch = sys.stdin.read(1)

                    # Ctrl+] to exit
                    if ch == "\x1d":
                        break

                    # Send to serial
                    try:
                        self._serial.write(ch.encode("utf-8"))
                    except Exception:
                        pass
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


class Terminal(AlyCommand):
    """Open UART serial terminal for hardware communication.

    This command provides an interactive serial terminal for communicating
    with FPGA boards and microcontrollers over UART. It supports auto-detection
    of common USB-UART chips and FPGA board interfaces.

    The terminal displays data received from the device and sends your
    keyboard input to the device. Press Ctrl+] to exit.

    Examples:
        aly terminal                           # Auto-detect port
        aly terminal --list                    # List available ports
        aly terminal --port COM3               # Windows: specific port
        aly terminal --port /dev/ttyUSB0       # Linux: specific port
        aly terminal --baud 9600               # Custom baud rate
        aly terminal --log session.log         # Log session to file
    """

    @staticmethod
    def add_parser(parser_adder):
        """Add terminal command parser."""
        parser = parser_adder.add_parser(
            "terminal",
            help="open UART serial terminal",
            description="Interactive serial terminal for FPGA/MCU communication. "
            "Press Ctrl+] to exit the terminal session.",
        )
        parser.add_argument(
            "--list",
            "-l",
            action="store_true",
            help="list available serial ports and exit",
        )
        parser.add_argument(
            "--port",
            "-p",
            help="serial port device (e.g., COM3, /dev/ttyUSB0). "
            "Auto-detected if not specified.",
        )
        parser.add_argument(
            "--baud",
            "-b",
            type=int,
            default=115200,
            help="baud rate (default: 115200)",
        )
        parser.add_argument(
            "--databits",
            type=int,
            choices=[5, 6, 7, 8],
            default=8,
            help="data bits (default: 8)",
        )
        parser.add_argument(
            "--parity",
            choices=["none", "even", "odd", "mark", "space"],
            default="none",
            help="parity (default: none)",
        )
        parser.add_argument(
            "--stopbits",
            type=float,
            choices=[1, 1.5, 2],
            default=1,
            help="stop bits (default: 1)",
        )
        parser.add_argument(
            "--log",
            type=Path,
            help="log session to file",
        )
        return parser

    def run(self, args, unknown_args):
        """Execute terminal command."""
        # Check pyserial is installed
        if not _check_pyserial():
            self.die(
                "pyserial is required for the terminal command.\n"
                "Install it with: pip install pyserial"
            )

        # List ports mode
        if args.list:
            ports = _list_serial_ports()
            if not ports:
                log.inf("No serial ports found")
                return 0

            log.banner("Available Serial Ports")
            for port in ports:
                print(f"  {port['device']}")
                if port["description"]:
                    print(f"    Description: {port['description']}")
                if port["manufacturer"]:
                    print(f"    Manufacturer: {port['manufacturer']}")
                print()
            return 0

        # Get port
        port = args.port
        if not port:
            port = _auto_detect_port()
            if not port:
                self.die(
                    "No serial port detected.\n"
                    "Use --port to specify one, or --list to see available ports."
                )
            log.inf(f"Auto-detected port: {port}")

        # Map parity names
        parity_map = {
            "none": "N",
            "even": "E",
            "odd": "O",
            "mark": "M",
            "space": "S",
        }
        parity = parity_map.get(args.parity, "N")

        # Create and run terminal
        log.banner("UART Terminal")

        terminal = SerialTerminal(
            port=port,
            baudrate=args.baud,
            bytesize=args.databits,
            parity=parity,
            stopbits=args.stopbits,
            log_file=args.log,
        )

        try:
            terminal.run()
        except RuntimeError as e:
            self.die(str(e))
        except KeyboardInterrupt:
            print("\nInterrupted.")

        return 0
