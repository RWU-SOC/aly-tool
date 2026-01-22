# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Main entry point for ALY command-line interface."""

import argparse
import sys
from pathlib import Path

from aly import __version__, log
from aly.commands import extension_commands, CommandError
from aly.app import BUILTIN_COMMANDS
from aly.util import find_aly_root


def main(argv=None):
    """Main entry point for ALY CLI."""
    if argv is None:
        argv = sys.argv[1:]

    # Create main parser
    parser = argparse.ArgumentParser(
        prog="aly",
        description="ALY - Advanced Logic Yieldflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
For more information, see: github.com/RWU-SOC/aly-tool/

Examples:
  aly init my-project          # Create new project
  aly info                     # Show configuration
  aly firmware                 # Build all firmware
  aly clean                    # Remove build artifacts
""",
    )

    parser.add_argument(
        "-V", "--version", action="version", version=f"ALY {__version__}"
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase verbosity (can be repeated: -v, -vv, -vvv)",
    )

    parser.add_argument(
        "-q", "--quiet", action="store_true", help="suppress non-error output"
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command", metavar="<command>", help="command to run"
    )

    # Register all commands
    commands = {}

    # Built-in commands
    for cmd_class in BUILTIN_COMMANDS:
        try:
            cmd = cmd_class()
            subparser = cmd.add_parser(subparsers)
            # Use the parser's prog name (e.g., "aly sim" -> "sim") as the key
            parser_name = subparser.prog.split()[-1] if subparser else cmd.name
            commands[parser_name] = cmd
        except Exception as e:
            log.wrn(f"Failed to register built-in command {cmd_class.__name__}: {e}")

    # Extension commands (only if in a project)
    project_root = find_aly_root()
    if project_root:
        for cmd in extension_commands(project_root):
            try:
                subparser = cmd.add_parser(subparsers)
                parser_name = subparser.prog.split()[-1] if subparser else cmd.name
                if parser_name in commands:
                    log.wrn(
                        f"Extension command '{parser_name}' overrides built-in command"
                    )
                commands[parser_name] = cmd
            except Exception as e:
                log.wrn(f"Failed to register extension command {cmd.name}: {e}")

    # Parse arguments
    args, unknown_args = parser.parse_known_args(argv)

    # Set verbosity
    if args.quiet:
        log.set_verbosity(0)
    else:
        log.set_verbosity(1 + args.verbose)

    # Check if command was specified
    if not args.command:
        parser.print_help()
        return 0

    # Get and run command
    cmd = commands.get(args.command)
    if not cmd:
        log.err(f"Unknown command: {args.command}")
        return 1

    # Set command context
    cmd.topdir = project_root

    # Run command
    try:
        return cmd.run(args, unknown_args) or 0
    except CommandError as e:
        log.err(f"Command failed: {e}")
        return e.returncode
    except KeyboardInterrupt:
        log.err("\nInterrupted")
        return 130
    except Exception as e:
        log.err(f"Unexpected error: {e}")
        if args.verbose >= 3:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
