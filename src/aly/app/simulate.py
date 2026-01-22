# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Simulation command for RTL workflow."""

import concurrent.futures
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

from aly.commands import AlyCommand
from aly import log
from aly.util import find_aly_root
from aly.config import ProjectConfig
from aly.sim_xsim import XsimBackend
from aly.sim_questa import QuestaBackend
from aly.sim_verilator import VerilatorBackend
from aly.fw_gcc import GccFirmwareBackend


def check_gtkwave() -> bool:
    """Check if GTKWave is installed and available in PATH."""
    return shutil.which("gtkwave") is not None


def launch_gtkwave(waveform_file: Path) -> bool:
    """Launch GTKWave with the given waveform file.

    Args:
        waveform_file: Path to VCD/WLF file to open

    Returns:
        True if GTKWave launched successfully, False otherwise.
    """

    try:
        proc = subprocess.Popen(
                    ["gtkwave", str(waveform_file)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
        try:
            proc.wait(timeout=2)
            # Process exited quickly - likely an error
            stderr = proc.stderr.read().decode() if proc.stderr else ""
            stdout = proc.stdout.read().decode() if proc.stdout else ""
            log.err(
                f"GTKWave GUI exited immediately (code {proc.returncode})"
            )
            if stderr:
                log.err(f"stderr: {stderr}")
            if stdout:
                log.err(f"stdout: {stdout}")
            return False
        except subprocess.TimeoutExpired:
            # Process is still running after 2s - GUI launched successfully
            log.success("GTKWave GUI Started")
            return True
        return True
    except FileNotFoundError:
        log.err("Failed to launch GTKWave: VCD file not found")
        return False


SIMULATOR_BACKENDS = {
    "xsim": XsimBackend,
    "questa": QuestaBackend,
    "modelsim": QuestaBackend,  # Alias
    "verilator": VerilatorBackend,
}


@dataclass
class TestResult:
    """Result of a single test."""

    name: str
    passed: bool
    duration: float
    log_file: Optional[Path]
    error: Optional[str]


class Simulate(AlyCommand):
    """Run RTL simulations (single test or regression)."""

    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            "sim",
            help="run RTL simulation(s)",
            description=(
                "Run RTL simulation with pluggable simulator backends. "
                "Supports single simulation or regression test suites."
            ),
        )
        parser.add_argument(
            "--tool",
            choices=list(SIMULATOR_BACKENDS.keys()),
            default="xsim",
            help="simulator to use (default: xsim)",
        )

        # Single simulation mode
        parser.add_argument(
            "--top", help="top module/testbench name (required for single simulation)"
        )
        parser.add_argument("--waves", action="store_true", help="enable waveform dump")
        parser.add_argument("--gui", action="store_true", help="open simulator GUI")
        parser.add_argument(
            "--plusargs", nargs="*", default=[], help="simulation plusargs"
        )
        parser.add_argument("--timeout", type=int, help="simulation timeout in seconds")
        parser.add_argument(
            "--show-log",
            action="store_true",
            help="display simulation log contents after completion"
        )
        parser.add_argument(
            "--gtkwave",
            action="store_true",
            help="open waveform in GTKWave after simulation (requires GTKWave installed)"
        )

        # Regression mode
        parser.add_argument(
            "--regress",
            action="store_true",
            help="run regression test suite",
        )
        parser.add_argument(
            "--suite", help="test suite name for regression (default: all tests)"
        )
        parser.add_argument(
            "--test",
            action="append",
            dest="tests",
            help=(
                "specific test(s) to run in regression (can be specified multiple times)"
            ),
        )
        parser.add_argument(
            "-j",
            "--jobs",
            type=int,
            default=1,
            help="number of parallel jobs for regression (default: 1)",
        )
        parser.add_argument(
            "--stop-on-fail",
            action="store_true",
            help="stop regression on first failure",
        )

        # List mode
        parser.add_argument(
            "--list",
            action="store_true",
            help="list available testbenches and exit",
        )
        parser.add_argument(
            "--list-tags",
            action="store_true",
            help="list testbenches grouped by tags",
        )
        parser.add_argument(
            "--list-suites",
            action="store_true",
            help="list available test suites and exit",
        )
        return parser

    def run(self, args, unknown_args):
        # List mode - show available testbenches or suites
        if args.list_suites:
            return self._list_testsuites(args)
        if args.list or args.list_tags:
            return self._list_testbenches(args)

        # Check GTKWave availability if requested
        if args.gtkwave and not check_gtkwave():
            self.die("GTKWave is not installed or not in PATH. Install GTKWave to use --gtkwave flag.")

        # --gtkwave implies --waves (need waveform to view)
        if args.gtkwave:
            args.waves = True

        # Determine mode
        if args.regress or args.suite or args.tests:
            return self._run_regression(args)
        else:
            if not args.top:
                self.die(
                    "--top is required for single simulation (or use --regress for regression mode)"
                )
            return self._run_single(args)

    def _build_firmware(self, firmware_dep: Dict, config: ProjectConfig, project_root: Path):
        """Build firmware dependency using GccFirmwareBackend directly.

        Args:
            firmware_dep: Dict with {name, type} where type="firmware"
            config: ProjectConfig instance
            project_root: Project root path

        Returns:
            Dict of mem_file_name -> mem_file_path
        """
        if not firmware_dep:
            return {}

        build_name = firmware_dep.get("name")
        if not build_name:
            log.wrn("No firmware build name specified")
            return {}

        log.inf(f"Building firmware: {build_name}")

        # Get the firmware build configuration
        fw_build = config.get_firmware(build_name)
        if not fw_build:
            log.err(f"Firmware build not found: {build_name}")
            return {}

        # Get toolchain configuration
        toolchain_name = fw_build.toolchain or (config.defaults.toolchain if config.defaults else None)
        if not toolchain_name or toolchain_name == "none":
            log.wrn("No firmware toolchain configured")
            return {}

        tc = config.get_toolchain(toolchain_name)
        if tc is None:
            log.err(f"Toolchain not found: {toolchain_name}")
            return {}

        tc_config = {
            "prefix": tc.prefix or f"{toolchain_name}-",
            "march": tc.march,
            "mabi": tc.mabi,
            "cpu": tc.cpu,
        }

        # Create backend and build
        backend = GccFirmwareBackend(tc_config, project_root)
        if not backend.check_toolchain():
            log.err(f"Toolchain not found: {tc_config['prefix']}gcc")
            return {}

        output_dir = project_root / "build" / "fw"
        result = backend.build(fw_build, output_dir)

        if not result.success:
            log.err(f"Firmware build failed: {result.stderr}")
            return {}

        return result.mem_files

    def _list_testsuites(self, args):
        """List available test suites."""
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        try:
            config = ProjectConfig.load(project_root)
        except Exception as e:
            self.die(f"Failed to load configuration: {e}")

        # Get all test suites
        suite_names = config.list_testsuites()
        suites = {name: config.get_testsuite(name) for name in suite_names}

        if not suites:
            log.inf("No test suites defined in project.")
            log.inf("Add testsuites in testbench manifest.yaml files")
            return 0

        log.banner(f"Test Suites ({len(suites)})")
        for name, suite in sorted(suites.items()):
            print(f"\n{log.Colors.BOLD}{name}{log.Colors.RESET}")
            if suite.description:
                print(f"  Description: {suite.description}")
            print(f"  Testbenches: {', '.join(suite.testbenches)}")
            print(f"  Parallel:    {suite.parallel}")
            print(f"  Timeout:     {suite.timeout}s")
            if suite.stop_on_fail:
                print("  Stop on fail: yes")

        return 0

    def _list_testbenches(self, args):
        """List available testbenches (main + IP tests)."""
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        try:
            config = ProjectConfig.load(project_root)
        except Exception as e:
            self.die(f"Failed to load configuration: {e}")

        # Get all tests (main + IP tests)
        testbenches = config.list_testbenches()
        tests = {name: config.get_testbench(name) for name in testbenches}

        # Separate project and IP testbenches using hybrid approach
        # Check both tag ("ip" tag) and location (ip/ directory)
        project_tests = {}
        ip_tests = {}

        for name, tb in tests.items():
            is_ip_test = False

            # Method 1: Check for "ip" tag
            if tb.tags and "ip" in tb.tags:
                is_ip_test = True

            # Method 2: Check if in ip/ directory
            if tb._manifest_path and "ip" in tb._manifest_path.parent.parts:
                is_ip_test = True

            if is_ip_test:
                ip_tests[name] = tb
            else:
                project_tests[name] = tb

        main_count = len(project_tests)
        ip_count = len(ip_tests)

        if not tests:
            log.inf("No testbenches defined in project.")
            log.inf("Add testbench manifests under tb/<name>/manifest.yaml")
            return 0

        if args.list_tags:
            # Group by tags
            log.banner("Testbenches by Tag")
            if ip_count > 0:
                print(
                    f"  {log.Colors.DIM}({main_count} project, {ip_count} from IPs){log.Colors.RESET}"
                )
            tags_map = {}
            untagged = []

            for name, test in tests.items():
                if test.tags:
                    for tag in test.tags:
                        if tag not in tags_map:
                            tags_map[tag] = []
                        tags_map[tag].append((name, test))
                else:
                    untagged.append((name, test))

            for tag in sorted(tags_map.keys()):
                print(f"\n{log.Colors.BOLD}[{tag}]{log.Colors.RESET}")
                for name, test in tags_map[tag]:
                    top = test.top_module
                    desc = f" - {test.description}" if test.description else ""
                    print(f"  {name} (top: {top}){desc}")

            if untagged:
                print(f"\n{log.Colors.BOLD}[untagged]{log.Colors.RESET}")
                for name, test in untagged:
                    top = test.top_module
                    desc = f" - {test.description}" if test.description else ""
                    print(f"  {name} (top: {top}){desc}")
        else:
            # Simple list
            log.banner(f"Available Testbenches ({len(tests)})")
            if ip_count > 0:
                print(
                    f"  {log.Colors.DIM}({main_count} project tests, {ip_count} IP tests){log.Colors.RESET}"
                )
            print()
            for name, test in sorted(tests.items()):
                top = test.top_module
                timeout = test.default_timeout
                tags = ", ".join(test.tags) if test.tags else "-"
                fw_deps = test.get_firmware_deps()
                fw = fw_deps[0].get("name", "-") if fw_deps else "-"
                desc = test.description or ""

                print(f"{log.Colors.BOLD}{name}{log.Colors.RESET}")
                print(f"  Top:      {top}")
                print(f"  Timeout:  {timeout}")
                print(f"  Tags:     {tags}")
                print(f"  Firmware: {fw}")
                if desc:
                    print(f"  Desc:     {desc}")
                print()

        return 0

    def _run_single(self, args):
        """Run a single simulation."""
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        # Load configuration
        try:
            config = ProjectConfig.load(project_root)
        except Exception as e:
            self.die(f"Failed to load configuration: {e}")

        # Get testbench
        tb = config.get_testbench(args.top)
        if not tb:
            self.die(f"Testbench not found: {args.top}")

        # Check if testbench requires firmware
        firmware_deps = tb.get_firmware_deps()
        for fw_dep in firmware_deps:
            mem_files = self._build_firmware(fw_dep, config, project_root)
            if mem_files:
                # Add memory file paths as plusargs
                if not hasattr(args, "plusargs") or args.plusargs is None:
                    args.plusargs = []
                for plusarg_name, mem_file in mem_files.items():
                    # Format: plusarg_name=value (without + prefix for --testplusarg)
                    # Convert path to POSIX format (forward slashes) for xsim compatibility
                    mem_file_posix = mem_file.as_posix()
                    plusarg = f"{plusarg_name}={mem_file_posix}"
                    args.plusargs.append(plusarg)
                    log.inf(f"Plusarg: +{plusarg}")

        # Get simulator backend
        backend_class = SIMULATOR_BACKENDS.get(args.tool)
        if not backend_class:
            self.die(f"Unsupported simulator: {args.tool}")

        tool_config = config.get_sim_tool(args.tool)
        self.dbg
        if not tool_config:
            self.die(f"No configuration for {args.tool} in workflow config")

        backend = backend_class(tool_config, project_root)

        # Setup output directory
        output_dir = project_root / "build" / "sim" / args.tool / args.top
        output_dir.mkdir(parents=True, exist_ok=True)

        log.banner(f"RTL Simulation: {args.top}")
        log.inf(f"Tool: {args.tool}")
        log.inf(f"Output: {output_dir}")

        # Collect RTL sources
        sources = []

        # 1. Resolve package dependencies first (must come before RTL modules)
        pkg_files = config.resolve_package_dep_files(tb)
        sources.extend(pkg_files)

        # 2. Resolve RTL/IP dependencies (returns UnitRef objects)
        rtl_dep_refs = config.resolve_rtl_deps(tb)
        for ref in rtl_dep_refs:
            module = ref.obj  # RTLModule
            manifest = ref.manifest  # RTLManifest

            # Get files for this specific module (packages + module files)
            sources.extend(manifest.get_files_for_module(module.name))

        # 3. Add testbench files
        sources.extend(tb.resolve_files())

        if not sources:
            self.die("No RTL sources found")

        log.inf(f"Found {len(sources)} source files")

        # Get includes and defines
        includes = []
        defines = {}

        # Get from dependencies (manifest-level includes and defines)
        for ref in rtl_dep_refs:
            manifest = ref.manifest  # RTLManifest
            includes.extend(manifest.get_include_dirs())
            defines.update(manifest.defines)

        # Get from testbench
        includes.extend(tb.get_include_dirs())
        defines.update(tb.defines)

        # Remove duplicates
        includes = list(set(includes))

        # Ensure SIMULATION is defined (without value for xvlog compatibility)
        if "SIMULATION" not in defines:
            defines["SIMULATION"] = ""

        # Compile
        log.inf("=== Compilation ===")
        if not backend.compile(sources, tb.top_module, output_dir, includes, defines):
            return 1

        # Elaborate
        log.inf("=== Elaboration ===")
        if not backend.elaborate(tb.top_module, output_dir):
            return 1

        # Simulate
        log.inf("=== Simulation ===")
        result = backend.simulate(
            tb.top_module,
            output_dir,
            waves=args.waves,
            gui=args.gui,
            plusargs=args.plusargs,
            timeout=args.timeout,
        )

        # Report results
        print()
        log.inf("=== Results ===")
        log.inf(f"Duration: {result.duration:.2f}s")
        log.inf(f"Log: {result.log_file}")

        if result.waveform_file:
            log.inf(f"Waveform: {result.waveform_file}")

        # Show log contents if requested
        if args.show_log and result.log_file and result.log_file.exists():
            print(f"\n{log.Colors.BOLD}=== Simulation Log ==={log.Colors.RESET}")
            with open(result.log_file, "r") as f:
                lines = f.readlines()
                # Show last 100 lines to avoid overwhelming output
                for line in lines[-100:]:
                    print(line.rstrip())

        # Launch GTKWave if requested
        if args.gtkwave:
            if result.waveform_file and result.waveform_file.exists():
                log.inf(f"Launching GTKWave: {result.waveform_file}")
                if launch_gtkwave(result.waveform_file):
                    log.success("GTKWave launched")
                else:
                    log.err("Failed to launch GTKWave")
            else:
                log.wrn("No waveform file generated, cannot open GTKWave")

        # Report pass/fail status
        if args.gui:
            log.inf("Simulation running in GUI mode (check results manually)")
            return 0
        elif result.success:
            log.success("Simulation PASSED")
            return 0
        else:
            log.err("Simulation FAILED")
            return 1

    def _run_regression(self, args):
        """Run regression test suite."""
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        # Load configuration
        try:
            config = ProjectConfig.load(project_root)
        except Exception as e:
            self.die(f"Failed to load configuration: {e}")

        # Get test list
        tests = self._get_test_list(config, args)

        if not tests:
            self.die("No tests found")

        log.banner(f"Regression: {len(tests)} tests")
        log.inf(f"Tool: {args.tool}")
        log.inf(f"Parallel jobs: {args.jobs}")

        # Run tests
        start_time = time.time()
        results = self._run_tests(tests, args.tool, config, project_root, args)
        total_duration = time.time() - start_time

        # Print summary
        self._print_summary(results, total_duration)

        # Return exit code
        failed = sum(1 for r in results if not r.passed)
        return 0 if failed == 0 else 1

    def _get_test_list(self, config: ProjectConfig, args) -> List[Dict]:
        """Get list of tests to run."""
        tests = []
        testbenches = config.list_testbenches()
        all_tests = {name: config.get_testbench(name) for name in testbenches}

        # If specific tests requested
        if args.tests:
            for test_name in args.tests:
                if test_name in all_tests:
                    test_cfg = all_tests[test_name]
                    tests.append(
                        {
                            "name": test_name,
                            "top": test_cfg.top_module,
                            "config": test_cfg,
                        }
                    )
                else:
                    log.wrn(f"Test not found: {test_name}")
        elif args.suite:
            # Get tests from a specific test suite
            suite = config.get_testsuite(args.suite)
            if not suite:
                log.wrn(f"Test suite not found: {args.suite}")
                return []

            for tb_name in suite.testbenches:
                test_cfg = all_tests.get(tb_name)
                if test_cfg:
                    tests.append(
                        {
                            "name": tb_name,
                            "top": test_cfg.top_module,
                            "config": test_cfg,
                        }
                    )
                else:
                    log.wrn(f"Testbench '{tb_name}' in suite '{args.suite}' not found")
        else:
            # Get all tests
            for test_name, test_cfg in all_tests.items():
                tests.append(
                    {
                        "name": test_name,
                        "top": test_cfg.top_module,
                        "config": test_cfg,
                    }
                )

        return tests

    def _run_tests(
        self,
        tests: List[Dict],
        tool: str,
        config: ProjectConfig,
        project_root: Path,
        args,
    ) -> List[TestResult]:
        """Run tests with optional parallelization."""
        results = []

        if args.jobs == 1:
            # Sequential execution
            for test in tests:
                result = self._run_single_test(test, tool, config, project_root, args)
                results.append(result)

                # Print status
                status = (
                    f"{log.Colors.GREEN}PASS{log.Colors.RESET}"
                    if result.passed
                    else f"{log.Colors.RED}FAIL{log.Colors.RESET}"
                )
                log.inf(f"[{status}] {result.name} ({result.duration:.2f}s)")

                if not result.passed and args.stop_on_fail:
                    log.wrn("Stopping on first failure")
                    break
        else:
            # Parallel execution
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=args.jobs
            ) as executor:
                futures = {
                    executor.submit(
                        self._run_single_test, test, tool, config, project_root, args
                    ): test
                    for test in tests
                }

                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.append(result)

                    # Print status
                    status = (
                        f"{log.Colors.GREEN}PASS{log.Colors.RESET}"
                        if result.passed
                        else f"{log.Colors.RED}FAIL{log.Colors.RESET}"
                    )
                    log.inf(f"[{status}] {result.name} ({result.duration:.2f}s)")

                    if not result.passed and args.stop_on_fail:
                        log.wrn("Stopping on first failure")
                        # Cancel remaining
                        for f in futures:
                            f.cancel()
                        break

        return results

    def _run_single_test(
        self, test: Dict, tool: str, config: ProjectConfig, project_root: Path, args
    ) -> TestResult:
        """Run a single test in regression mode."""
        name = test["name"]
        top = test["top"]
        test_cfg = test["config"]  # TestConfig dataclass

        log.dbg(f"Running test: {name}")

        start_time = time.time()

        try:
            # Get backend
            backend_class = SIMULATOR_BACKENDS.get(tool)
            if not backend_class:
                raise ValueError(f"Unknown simulator: {tool}")

            tool_config = config.get_sim_tool(tool)
            if not tool_config:
                raise ValueError(f"No configuration for {tool} in workflow config")

            backend = backend_class(tool_config, project_root)

            # Get testbench
            tb = config.get_testbench(name)
            if not tb:
                raise ValueError(f"Testbench not found: {name}")

            # Collect RTL sources
            sources = []

            # 1. Resolve package dependencies first (must come before RTL modules)
            pkg_files = config.resolve_package_dep_files(tb)
            sources.extend(pkg_files)

            # 2. Resolve RTL/IP dependencies (returns UnitRef objects)
            rtl_dep_refs = config.resolve_rtl_deps(tb)
            for ref in rtl_dep_refs:
                module = ref.obj  # RTLModule
                manifest = ref.manifest  # RTLManifest

                # Get files for this specific module (packages + module files)
                sources.extend(manifest.get_files_for_module(module.name))

            # 3. Add testbench files
            sources.extend(tb.resolve_files())

            # Get includes and defines
            includes = []
            defines = {}

            # Get from dependencies (manifest-level includes and defines)
            for ref in rtl_dep_refs:
                manifest = ref.manifest  # RTLManifest
                includes.extend(manifest.get_include_dirs())
                defines.update(manifest.defines)

            # Get from testbench
            includes.extend(tb.get_include_dirs())
            defines.update(tb.defines)

            # Remove duplicates
            includes = list(set(includes))

            # Setup output directory
            output_dir = project_root / "build" / "regress" / tool / name
            output_dir.mkdir(parents=True, exist_ok=True)

            # Ensure SIMULATION is defined
            if "SIMULATION" not in defines:
                defines["SIMULATION"] = ""

            # Add testbench-specific defines
            if test_cfg.defines:
                defines.update(test_cfg.defines)

            # Compile
            success = backend.compile(
                sources=sources,
                top=top,
                output_dir=output_dir,
                includes=includes,
                defines=defines,
            )

            if not success:
                raise RuntimeError("Compilation failed")

            # Elaborate
            success = backend.elaborate(top=top, output_dir=output_dir)

            if not success:
                raise RuntimeError("Elaboration failed")

            # Simulate
            timeout = test_cfg.default_timeout or args.timeout or 300
            plusargs = test_cfg.plusargs  # Already a dict

            result = backend.simulate(
                top=top,
                output_dir=output_dir,
                waves=args.waves,
                gui=False,  # Never use GUI in regression
                plusargs=[f"{k}={v}" for k, v in plusargs.items()] if plusargs else [],
                timeout=timeout,
            )

            duration = time.time() - start_time

            return TestResult(
                name=name,
                passed=result.success,
                duration=duration,
                log_file=result.log_file,
                error=None,
            )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=name, passed=False, duration=duration, log_file=None, error=str(e)
            )

    def _print_summary(self, results: List[TestResult], total_duration: float):
        """Print regression summary."""
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        total = len(results)

        log.banner("Regression Summary")
        log.inf(f"Total tests: {total}")
        log.inf(f"Passed: {log.Colors.GREEN}{passed}{log.Colors.RESET}")
        log.inf(f"Failed: {log.Colors.RED}{failed}{log.Colors.RESET}")
        log.inf(f"Duration: {total_duration:.2f}s")

        if failed > 0:
            log.wrn("\nFailed tests:")
            for r in results:
                if not r.passed:
                    log.err(f"  - {r.name}")
                    if r.error:
                        log.err(f"    Error: {r.error}")
                    if r.log_file:
                        log.err(f"    Log: {r.log_file}")

