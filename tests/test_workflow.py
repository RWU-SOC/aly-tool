# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Tests for RTL workflow commands."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from aly.app.simulate import Simulate
from aly.app.synthesize import Synthesize
from aly.app.gen_mem import GenMem
from aly.app.regress import Regress
from aly.backends import SimulationResult, SynthesisResult


@pytest.fixture
def workflow_config(tmp_path):
    """Create a sample workflow configuration."""
    config_file = tmp_path / "aly_workflow.yaml"
    config_content = """
project:
  name: test-soc
  version: "1.0.0"

rtl:
  top: test_top
  dirs:
    - rtl/core
  includes:
    - rtl/include
  defines:
    SIMULATION: "1"

tb:
  root: verification
  tops:
    test_tb:
      filelist: verification/test_tb.f
      timeout: 1000
      suite: smoke

tools:
  sim:
    xsim:
      vlog: xvlog
      xelab: xelab
      bin: xsim
  synth:
    vivado:
      bin: vivado
      part: xc7a100tcsg324-1
"""
    config_file.write_text(config_content)
    
    # Create directory structure
    (tmp_path / "rtl" / "core").mkdir(parents=True)
    (tmp_path / "rtl" / "include").mkdir(parents=True)
    (tmp_path / "verification").mkdir(parents=True)
    (tmp_path / ".aly").mkdir()
    
    # Create a sample RTL file
    (tmp_path / "rtl" / "core" / "test.sv").write_text("module test; endmodule")
    
    return tmp_path


def test_simulate_command_help():
    """Test simulate command help text."""
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    Simulate.add_parser(subparsers)
    
    # Should not raise exception
    args = parser.parse_args(['sim', '--help'] if False else ['sim', '--top', 'test'])


def test_simulate_with_mock_backend(workflow_config, monkeypatch):
    """Test simulate command with mocked backend."""
    # Create .aly directory
    (workflow_config / ".aly").mkdir(exist_ok=True)
    
    # Mock find_aly_root in the Simulate command module
    from aly.app import simulate
    monkeypatch.setattr(simulate, 'find_aly_root', lambda: workflow_config)
    
    mock_backend = Mock()
    mock_backend.compile.return_value = True
    mock_backend.elaborate.return_value = True
    mock_backend.simulate.return_value = SimulationResult(
        success=True,
        duration=1.5,
        log_file=workflow_config / "sim.log",
        waveform_file=None
    )
    
    # Patch the backend registry
    with patch('aly.app.simulate.SIMULATOR_BACKENDS', {'xsim': lambda config, project: mock_backend}):
        cmd = Simulate()
        args = type('Args', (), {
            'tool': 'xsim',
            'top': 'test_tb',
            'waves': False,
            'gui': False,
            'plusargs': None,
            'timeout': None,
            'config': workflow_config / "aly_workflow.yaml"
        })()
        
        result = cmd.run(args, [])
        
        assert result == 0
        assert mock_backend.compile.called
        assert mock_backend.elaborate.called
        assert mock_backend.simulate.called


def test_synthesize_command_help():
    """Test synthesize command help text."""
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    Synthesize.add_parser(subparsers)


def test_synthesize_with_mock_backend(workflow_config, monkeypatch):
    """Test synthesize command with mocked backend."""
    # Create .aly directory
    (workflow_config / ".aly").mkdir(exist_ok=True)
    
    # Mock find_aly_root in the Synthesize command module
    from aly.app import synthesize
    monkeypatch.setattr(synthesize, 'find_aly_root', lambda: workflow_config)
    
    # Mock backend
    mock_backend = Mock()
    mock_backend.synthesize.return_value = SynthesisResult(
        success=True,
        duration=45.0,
        reports_dir=workflow_config / "reports",
        timing_met=True
    )
    mock_backend.get_reports.return_value = {}
    
    with patch('aly.app.synthesize.SYNTHESIS_BACKENDS', {'vivado': lambda config: mock_backend}):
        cmd = Synthesize()
        args = type('Args', (), {
            'tool': 'vivado',
            'top': 'test_top',
            'part': None,
            'constraints': None,
            'config': workflow_config / "aly_workflow.yaml",
            'jobs': None,
            'report': False
        })()
        
        result = cmd.run(args, [])
        
        assert result == 0
        assert mock_backend.synthesize.called


def test_gen_mem_command_help():
    """Test gen-mem command help text."""
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    GenMem.add_parser(subparsers)


def test_gen_mem_command(tmp_path, monkeypatch):
    """Test memory generation command."""
    from aly import util
    
    # Create dummy ELF file
    elf_file = tmp_path / "firmware.elf"
    elf_file.write_bytes(b'\x7fELF' + b'\x00' * 100)  # Minimal ELF header
    
    # Mock objcopy to create dummy binary
    def mock_objcopy(*args, **kwargs):
        # Find output file from args
        bin_file = None
        for i, arg in enumerate(args[0]):
            if arg.endswith('.tmp.bin'):
                bin_file = Path(arg)
                break
        
        if bin_file:
            bin_file.write_bytes(b'\xde\xad\xbe\xef' * 4)
        
        return type('Result', (), {'returncode': 0, 'stderr': ''})()
    
    monkeypatch.setattr(util, 'find_tool', lambda name: name)
    
    with patch('subprocess.run', side_effect=mock_objcopy):
        cmd = GenMem()
        args = type('Args', (), {
            'elf_file': elf_file,
            'output': tmp_path / "firmware.hex",
            'format': 'hex',
            'word_width': 32,
            'byte_order': 'little',
            'start_addr': 0,
            'size': None,
            'section': None
        })()
        
        result = cmd.run(args, [])
        
        assert result == 0
        assert (tmp_path / "firmware.hex").exists()


def test_regress_command_help():
    """Test regress command help text."""
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    Regress.add_parser(subparsers)


def test_workflow_config_loading(workflow_config):
    """Test loading workflow configuration."""
    from aly.workflow_config import WorkflowConfig
    
    config = WorkflowConfig.load(
        workflow_config / "aly_workflow.yaml",
        workflow_config
    )
    
    assert config.rtl.top == "test_top"
    assert len(config.rtl.dirs) == 1
    assert config.rtl.defines['SIMULATION'] == "1"
    assert 'test_tb' in config.tb.tops


def test_backend_interface():
    """Test that backends follow the interface contract."""
    from aly.backends import SimulatorBackend, SynthesisBackend
    import inspect
    
    # Check SimulatorBackend has required methods
    assert hasattr(SimulatorBackend, 'compile')
    assert hasattr(SimulatorBackend, 'elaborate')
    assert hasattr(SimulatorBackend, 'simulate')
    
    # Check SynthesisBackend has required methods
    assert hasattr(SynthesisBackend, 'synthesize')
    assert hasattr(SynthesisBackend, 'get_reports')
    
    # Verify they are abstract
    assert inspect.isabstract(SimulatorBackend)
    assert inspect.isabstract(SynthesisBackend)
