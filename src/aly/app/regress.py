# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Regression test runner command."""

import argparse
import concurrent.futures
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

from aly.commands import AlyCommand
from aly import log
from aly.util import find_aly_root
from aly.workflow_config import WorkflowConfig
from aly.app.simulate import SIMULATOR_BACKENDS


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    duration: float
    log_file: Optional[Path]
    error: Optional[str]


class Regress(AlyCommand):
    """Run regression test suites."""
    
    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            'regress',
            help='run regression tests',
            description='Run regression test suite with specified simulator'
        )
        
        parser.add_argument(
            '--suite',
            help='test suite name (default: all tests)'
        )
        
        parser.add_argument(
            '--tool',
            choices=list(SIMULATOR_BACKENDS.keys()),
            default='xsim',
            help='simulator tool to use'
        )
        
        parser.add_argument(
            '--test',
            action='append',
            dest='tests',
            help='specific test to run (can be specified multiple times)'
        )
        
        parser.add_argument(
            '-j', '--jobs',
            type=int,
            default=1,
            help='number of parallel jobs (default: 1)'
        )
        
        parser.add_argument(
            '--waves',
            action='store_true',
            help='enable waveform capture for all tests'
        )
        
        parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='test timeout in seconds (default: 300)'
        )
        
        parser.add_argument(
            '--stop-on-fail',
            action='store_true',
            help='stop regression on first failure'
        )
        
        parser.add_argument(
            '--config',
            type=Path,
            help='path to workflow config (default: aly_workflow.yaml)'
        )
        
        return parser
    
    def run(self, args, unknown_args):
        # Find project root
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")
        
        # Load configuration
        config_path = args.config or project_root / 'aly_workflow.yaml'
        if not config_path.exists():
            self.die(f"Workflow config not found: {config_path}")
        
        try:
            config = WorkflowConfig.load(config_path, project_root)
        except Exception as e:
            self.die(f"Failed to load config: {e}")
        
        # Get test list
        tests = self._get_test_list(config, args)
        
        if not tests:
            self.die("No tests found")
        
        log.banner(f"Regression: {len(tests)} tests")
        log.inf(f"Tool: {args.tool}")
        log.inf(f"Parallel jobs: {args.jobs}")
        
        # Run tests
        start_time = time.time()
        results = self._run_tests(
            tests=tests,
            tool=args.tool,
            config=config,
            project_root=project_root,
            args=args
        )
        total_duration = time.time() - start_time
        
        # Print summary
        self._print_summary(results, total_duration)
        
        # Return exit code
        failed = sum(1 for r in results if not r.passed)
        return 0 if failed == 0 else 1
    
    def _get_test_list(self, config: WorkflowConfig, args) -> List[Dict]:
        """
        Get list of tests to run.
        
        Args:
            config: Workflow configuration
            args: Command arguments
            
        Returns:
            List of test dictionaries
        """
        tests = []
        
        # If specific tests requested
        if args.tests:
            for test_name in args.tests:
                if test_name in config.tb.tops:
                    tests.append({
                        'name': test_name,
                        'top': test_name,
                        'config': config.tb.tops[test_name]
                    })
                else:
                    log.wrn(f"Test not found in config: {test_name}")
        else:
            # Get all tests from config
            for top_name, top_config in config.tb.tops.items():
                # Apply suite filter if specified
                suite = top_config.get('suite', 'default')
                if args.suite and suite != args.suite:
                    continue
                
                tests.append({
                    'name': top_name,
                    'top': top_name,
                    'config': top_config
                })
        
        return tests
    
    def _run_tests(
        self,
        tests: List[Dict],
        tool: str,
        config: WorkflowConfig,
        project_root: Path,
        args
    ) -> List[TestResult]:
        """
        Run tests with optional parallelization.
        
        Args:
            tests: List of test dictionaries
            tool: Simulator tool name
            config: Workflow configuration
            project_root: Project root directory
            args: Command arguments
            
        Returns:
            List of TestResult objects
        """
        results = []
        
        if args.jobs == 1:
            # Sequential execution
            for test in tests:
                result = self._run_single_test(
                    test, tool, config, project_root, args
                )
                results.append(result)
                
                # Print status
                status = f"{log.Colors.GREEN}PASS{log.Colors.RESET}" if result.passed else f"{log.Colors.RED}FAIL{log.Colors.RESET}"
                log.inf(f"[{status}] {result.name} ({result.duration:.2f}s)")
                
                if not result.passed and args.stop_on_fail:
                    log.wrn("Stopping on first failure")
                    break
        else:
            # Parallel execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
                futures = {
                    executor.submit(
                        self._run_single_test,
                        test, tool, config, project_root, args
                    ): test
                    for test in tests
                }
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.append(result)
                    
                    # Print status
                    status = f"{log.Colors.GREEN}PASS{log.Colors.RESET}" if result.passed else f"{log.Colors.RED}FAIL{log.Colors.RESET}"
                    log.inf(f"[{status}] {result.name} ({result.duration:.2f}s)")
                    
                    if not result.passed and args.stop_on_fail:
                        log.wrn("Stopping on first failure")
                        # Cancel remaining
                        for f in futures:
                            f.cancel()
                        break
        
        return results
    
    def _run_single_test(
        self,
        test: Dict,
        tool: str,
        config: WorkflowConfig,
        project_root: Path,
        args
    ) -> TestResult:
        """
        Run a single test.
        
        Args:
            test: Test dictionary
            tool: Simulator tool
            config: Workflow configuration
            project_root: Project root
            args: Command arguments
            
        Returns:
            TestResult object
        """
        name = test['name']
        top = test['top']
        test_config = test['config']
        
        log.dbg(f"Running test: {name}")
        
        start_time = time.time()
        
        try:
            # Get backend
            backend_class = SIMULATOR_BACKENDS.get(tool)
            if not backend_class:
                raise ValueError(f"Unknown simulator: {tool}")
            
            backend = backend_class(config)
            
            # Get sources
            sources = config.get_rtl_files()
            
            # Add testbench sources from filelist if specified
            if 'filelist' in test_config:
                filelist = project_root / test_config['filelist']
                if filelist.exists():
                    with open(filelist, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                tb_file = project_root / line
                                if tb_file.exists():
                                    sources.append(tb_file)
            
            # Setup output directory
            output_dir = project_root / '.aly_build' / 'regress' / tool / name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Compile
            success = backend.compile(
                sources=sources,
                top=top,
                output_dir=output_dir,
                includes=config.rtl.includes,
                defines=config.rtl.defines
            )
            
            if not success:
                raise RuntimeError("Compilation failed")
            
            # Elaborate
            success = backend.elaborate(
                top=top,
                output_dir=output_dir
            )
            
            if not success:
                raise RuntimeError("Elaboration failed")
            
            # Simulate
            timeout = test_config.get('timeout', args.timeout)
            plusargs = test_config.get('plusargs', [])
            
            result = backend.simulate(
                top=top,
                output_dir=output_dir,
                waves=args.waves,
                gui=False,  # Never use GUI in regression
                plusargs=plusargs,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            return TestResult(
                name=name,
                passed=result.success,
                duration=duration,
                log_file=result.log_file,
                error=None
            )
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=name,
                passed=False,
                duration=duration,
                log_file=None,
                error=str(e)
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
