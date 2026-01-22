# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Synthesis command for RTL workflow.

This module provides RTL synthesis capabilities using various backends:
- Vivado (Xilinx)
- Yosys (open-source)
- Genus (Cadence)

Architecture:
    The Synthesize command discovers RTL sources from the project configuration
    using the UnitRef pattern for dependency resolution, then runs the selected
    synthesis tool.

Usage:
    aly synth --module cpu --tool vivado --part xc7a100tcsg324-1
    aly synth --module uart --tool yosys --part generic
    aly synth --module core --tool genus --part sky130
"""

import argparse
from pathlib import Path
from typing import List, Dict

from aly.commands import AlyCommand
from aly import log
from aly.util import find_aly_root
from aly.config import ProjectConfig
from aly.synth_vivado import VivadoBackend
from aly.synth_yosys import YosysBackend


SYNTHESIS_BACKENDS = {
    "vivado": VivadoBackend,
    "yosys": YosysBackend,
}


class Synthesize(AlyCommand):
    """Run RTL synthesis.

    This command reads RTL configuration from manifest.yaml files to find
    source files, include directories, and defines. It uses the UnitRef
    pattern for dependency resolution.

    Examples:
        aly synth --module cpu --tool vivado --part xc7a100tcsg324-1
        aly synth --module uart --tool yosys --part generic
    """

    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            "synth",
            help="run RTL synthesis",
            description="Synthesize RTL design with specified tool",
        )

        parser.add_argument(
            "--module",
            "-m",
            help="RTL module name for synthesis (required)",
        )

        parser.add_argument(
            "--tool",
            choices=list(SYNTHESIS_BACKENDS.keys()),
            default="vivado",
            help="synthesis tool to use",
        )

        parser.add_argument("--top", help="top module name (default: from module config)")

        parser.add_argument(
            "--part",
            help="FPGA part or technology library (e.g., xc7a100tcsg324-1, sky130)",
        )

        parser.add_argument(
            "--constraints",
            nargs="+",
            help="constraint files (XDC for Vivado, SDC for others)",
        )

        parser.add_argument(
            "-j",
            "--jobs",
            type=int,
            help="number of parallel jobs (if supported by tool)",
        )

        parser.add_argument(
            "--report", action="store_true", help="print synthesis reports"
        )

        return parser

    def run(self, args, unknown_args):
        # Find project root
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project (no .aly directory found)")

        # Load configuration
        try:
            config = ProjectConfig.load(project_root)
        except Exception as e:
            self.die(f"Failed to load config: {e}")

        # Require --module
        if not args.module:
            self.die("Module name required with --module")

        # Get RTL module using UnitRef pattern
        rtl_module = config.get_rtl_module(args.module)
        if not rtl_module:
            self.die(f"RTL module not found: {args.module}")

        # Get top module name (fallback to module name if not specified)
        top = args.top or rtl_module.obj.top or rtl_module.obj.name

        log.banner(f"Synthesis: {top}")
        log.inf(f"Tool: {args.tool}")
        log.inf(f"Module: {args.module}")

        # Collect sources using dependency resolution (same pattern as lint.py)
        sources: List[Path] = []
        includes: List[Path] = []
        defines: Dict[str, str] = {}

        # 1. Resolve package dependencies first (must come before RTL modules)
        pkg_files = config.resolve_package_dep_files(rtl_module.obj)
        sources.extend(pkg_files)

        # 2. Resolve RTL/IP dependencies (returns UnitRef objects in topological order)
        rtl_dep_refs = config.resolve_rtl_deps(rtl_module.obj)
        for ref in rtl_dep_refs:
            module = ref.obj  # RTLModule
            manifest = ref.manifest  # RTLManifest

            # Get files for this specific module (packages + module files)
            sources.extend(manifest.get_files_for_module(module.name))
            includes.extend(manifest.get_include_dirs())
            defines.update(manifest.get_defines())

        # 3. Add RTL module files
        sources.extend(rtl_module.obj.resolve_files())

        # 4. Add includes/defines from module's parent manifest
        includes.extend(rtl_module.manifest.get_include_dirs())
        defines.update(rtl_module.manifest.get_defines())

        if not sources:
            self.die("No RTL sources found")

        log.inf(f"Found {len(sources)} RTL files")

        # Setup output directory
        output_dir = project_root / "build" / "synth" / args.tool / args.module
        output_dir.mkdir(parents=True, exist_ok=True)
        log.dbg(f"Output directory: {output_dir}")

        # Get constraint files
        constraints = []
        if args.constraints:
            # Load constraint manager for name resolution
            from aly.app.constraints import ConstraintManager
            constraint_mgr = ConstraintManager(project_root, config)
            constraint_mgr.load()

            for c in args.constraints:
                # Try resolving as constraint set name first
                named_files = constraint_mgr.get_constraint_files(c)
                if named_files:
                    log.inf(f"Using constraint set '{c}': {len(named_files)} files")
                    constraints.extend(named_files)
                else:
                    # Fall back to treating as file path
                    constraint_path = Path(c)
                    if not constraint_path.is_absolute():
                        constraint_path = project_root / constraint_path
                    if not constraint_path.exists():
                        log.wrn(f"Constraint file/set not found: {c}")
                    else:
                        constraints.append(constraint_path)

        # Get backend
        backend_class = SYNTHESIS_BACKENDS.get(args.tool)
        if not backend_class:
            self.die(f"Unknown synthesis tool: {args.tool}")

        # Get tool config
        tool_config = config.synth.get_tool_config(args.tool)

        try:
            backend = backend_class(tool_config, project_root)
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
                includes=list(set(includes)),
                defines=defines,
                jobs=args.jobs,
            )
        except Exception as e:
            self.die(f"Synthesis failed: {e}")

        # Print results
        if result.success:
            log.success(f"Synthesis completed in {result.duration:.2f}s")

            if result.timing_met is not None:
                if result.timing_met:
                    log.success("Timing constraints MET")
                else:
                    log.wrn("Timing constraints NOT MET")

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
                                with open(path, "r") as f:
                                    content = f.read(1000)  # First 1000 chars
                                    print(content)
                                    if len(content) == 1000:
                                        print("... (truncated)")
                            except:
                                pass

            log.inf(f"Results in: {output_dir}")
            return 0
        else:
            log.err("Synthesis FAILED")
            log.inf(f"Check logs in: {output_dir}")
            return 1
