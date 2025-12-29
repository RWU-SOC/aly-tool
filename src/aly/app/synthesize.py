# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthesis command for RTL workflow."""

import argparse
from pathlib import Path
from typing import Optional

from aly.commands import AlyCommand
from aly import log
from aly.util import find_aly_root
from aly.workflow_config import WorkflowConfig
from aly.synth_vivado import VivadoBackend
from aly.synth_yosys import YosysBackend


SYNTHESIS_BACKENDS = {
    'vivado': VivadoBackend,
    'yosys': YosysBackend,
}


class Synthesize(AlyCommand):
    """Run RTL synthesis."""
    
    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            'synth',
            help='run RTL synthesis',
            description='Synthesize RTL design with specified tool'
        )
        
        parser.add_argument(
            '--tool',
            choices=list(SYNTHESIS_BACKENDS.keys()),
            default='vivado',
            help='synthesis tool to use'
        )
        
        parser.add_argument(
            '--top',
            help='top module name (default: from config)'
        )
        
        parser.add_argument(
            '--part',
            help='FPGA part or technology library (e.g., xc7a100tcsg324-1, sky130)'
        )
        
        parser.add_argument(
            '--constraints',
            nargs='+',
            help='constraint files (XDC for Vivado, SDC for others)'
        )
        
        parser.add_argument(
            '--config',
            type=Path,
            help='path to workflow config (default: aly_workflow.yaml)'
        )
        
        parser.add_argument(
            '-j', '--jobs',
            type=int,
            help='number of parallel jobs (if supported by tool)'
        )
        
        parser.add_argument(
            '--report',
            action='store_true',
            help='print synthesis reports'
        )
        
        return parser
    
    def run(self, args, unknown_args):
        # Find project root
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project (no .aly directory found)")
        
        # Load configuration
        config_path = args.config or project_root / 'aly_workflow.yaml'
        if not config_path.exists():
            self.die(f"Workflow config not found: {config_path}")
        
        try:
            config = WorkflowConfig.load(config_path, project_root)
        except Exception as e:
            self.die(f"Failed to load config: {e}")
        
        # Get top module
        top = args.top or config.rtl.top
        if not top:
            self.die("Top module not specified (use --top or set in config)")
        
        log.banner(f"Synthesis: {top}")
        log.inf(f"Tool: {args.tool}")
        
        # Get RTL sources
        try:
            sources = config.get_rtl_files()
            log.inf(f"Found {len(sources)} RTL files")
        except Exception as e:
            self.die(f"Failed to gather RTL sources: {e}")
        
        # Setup output directory
        output_dir = project_root / '.aly_build' / 'synth' / args.tool / top
        output_dir.mkdir(parents=True, exist_ok=True)
        log.dbg(f"Output directory: {output_dir}")
        
        # Get constraint files
        constraints = []
        if args.constraints:
            for c in args.constraints:
                constraint_path = Path(c)
                if not constraint_path.is_absolute():
                    constraint_path = project_root / constraint_path
                if not constraint_path.exists():
                    log.wrn(f"Constraint file not found: {constraint_path}")
                else:
                    constraints.append(constraint_path)
        
        # Get backend
        backend_class = SYNTHESIS_BACKENDS.get(args.tool)
        if not backend_class:
            self.die(f"Unknown synthesis tool: {args.tool}")
        
        try:
            backend = backend_class(config)
        except Exception as e:
            self.die(f"Failed to initialize {args.tool} backend: {e}")
        
        # Run synthesis
        try:
            result = backend.synthesize(
                sources=sources,
                top=top,
                output_dir=output_dir,
                part=args.part,
                constraints=constraints if constraints else None,
                includes=config.rtl.includes,
                defines=config.rtl.defines
            )
        except Exception as e:
            self.die(f"Synthesis failed: {e}")
        
        # Print results
        if result.success:
            log.success(f"✓ Synthesis completed in {result.duration:.2f}s")
            
            if result.timing_met is not None:
                if result.timing_met:
                    log.success("✓ Timing constraints MET")
                else:
                    log.wrn("✗ Timing constraints NOT MET")
            
            # Print reports if requested
            if args.report:
                reports = backend.get_reports(output_dir)
                if reports:
                    log.banner("Synthesis Reports")
                    for name, path in reports.items():
                        log.inf(f"{name}: {path}")
                        # Optionally print summary
                        if path.exists() and path.stat().st_size < 100000:  # < 100KB
                            try:
                                with open(path, 'r') as f:
                                    content = f.read(1000)  # First 1000 chars
                                    print(content)
                                    if len(content) == 1000:
                                        print("... (truncated)")
                            except:
                                pass
            
            log.inf(f"Results in: {output_dir}")
            return 0
        else:
            log.err("✗ Synthesis FAILED")
            log.inf(f"Check logs in: {output_dir}")
            return 1
