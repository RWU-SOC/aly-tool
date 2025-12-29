# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Simulation command for RTL workflow."""

import argparse
from pathlib import Path
from typing import Optional

from aly.commands import AlyCommand
from aly import log
from aly.util import find_aly_root
from aly.workflow_config import WorkflowConfig
from aly.sim_xsim import XsimBackend
from aly.sim_questa import QuestaBackend
from aly.sim_verilator import VerilatorBackend


SIMULATOR_BACKENDS = {
    'xsim': XsimBackend,
    'questa': QuestaBackend,
    'modelsim': QuestaBackend,  # Alias
    'verilator': VerilatorBackend,
}


class Simulate(AlyCommand):
    """Run RTL simulations."""
    
    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            'sim',
            help='run RTL simulation',
            description='Run RTL simulation with pluggable simulator backends'
        )
        parser.add_argument(
            '--tool',
            choices=list(SIMULATOR_BACKENDS.keys()),
            default='xsim',
            help='simulator to use (default: xsim)'
        )
        parser.add_argument(
            '--top',
            required=True,
            help='top module/testbench name'
        )
        parser.add_argument(
            '--waves',
            action='store_true',
            help='enable waveform dump'
        )
        parser.add_argument(
            '--gui',
            action='store_true',
            help='open simulator GUI'
        )
        parser.add_argument(
            '--plusargs',
            nargs='*',
            default=[],
            help='simulation plusargs'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            help='simulation timeout in seconds'
        )
        parser.add_argument(
            '--config',
            default='aly_workflow.yaml',
            help='workflow configuration file (default: aly_workflow.yaml)'
        )
        return parser
    
    def run(self, args, unknown_args):
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")
        
        # Load configuration
        config_path = project_root / args.config
        if not config_path.exists():
            self.die(f"Configuration file not found: {config_path}\nRun 'aly init' to create it")
        
        try:
            config = WorkflowConfig.load(config_path, project_root)
        except Exception as e:
            self.die(f"Failed to load configuration: {e}")
        
        # Get simulator backend
        backend_class = SIMULATOR_BACKENDS.get(args.tool)
        if not backend_class:
            self.die(f"Unsupported simulator: {args.tool}")
        
        tool_config = config.get_sim_tool(args.tool)
        if not tool_config:
            self.die(f"No configuration for {args.tool} in {config_path}")
        
        backend = backend_class(tool_config, project_root)
        
        # Setup output directory
        output_dir = project_root / '.aly_build' / 'sim' / args.tool / args.top
        output_dir.mkdir(parents=True, exist_ok=True)
        
        log.banner(f"RTL Simulation: {args.top}")
        log.inf(f"Tool: {args.tool}")
        log.inf(f"Output: {output_dir}")
        
        # Get RTL sources
        sources = config.get_rtl_files()
        if not sources:
            self.wrn("No RTL sources found")
        
        log.inf(f"Found {len(sources)} RTL files")
        
        # Get includes and defines
        includes = [config.resolve_path(inc) for inc in config.rtl.includes]
        defines = config.rtl.defines
        
        # Compile
        log.inf("=== Compilation ===")
        if not backend.compile(sources, args.top, output_dir, includes, defines):
            return 1
        
        # Elaborate
        log.inf("=== Elaboration ===")
        if not backend.elaborate(args.top, output_dir):
            return 1
        
        # Simulate
        log.inf("=== Simulation ===")
        result = backend.simulate(
            args.top,
            output_dir,
            waves=args.waves,
            gui=args.gui,
            plusargs=args.plusargs,
            timeout=args.timeout
        )
        
        # Report results
        print()
        log.inf("=== Results ===")
        log.inf(f"Duration: {result.duration:.2f}s")
        log.inf(f"Log: {result.log_file}")
        
        if result.waveform_file:
            log.inf(f"Waveform: {result.waveform_file}")
        
        if result.success:
            log.success("Simulation PASSED")
            return 0
        else:
            log.err("Simulation FAILED")
            return 1
