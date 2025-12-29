# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Init command - creates new ALY projects."""

import argparse
from pathlib import Path

from aly import log
from aly.commands import AlyCommand


PROJECT_TEMPLATES = {
    'soc': {
        'description': 'Full SoC project with RTL, firmware, and verification',
        'structure': {
            '.aly': {
                'config': '',
                'commands.yml': '''# Custom ALY commands for this project
# See https://aly.readthedocs.io/extensions
aly-commands: []
'''
            },
            'aly_workflow.yaml': '''# ALY Workflow Configuration
# RTL simulation, synthesis, and verification workflow

project:
  name: my-soc
  version: "1.0.0"

rtl:
  top: soc_top
  dirs:
    - rtl/core
    - rtl/peripherals
    - rtl/interconnect
    - rtl/soc
  includes:
    - rtl/include
  defines:
    SIMULATION: "1"

tb:
  root: verification
  tops:
    soc_tb:
      filelist: verification/integration/soc_tb.f
      timeout: 10000
    core_tb:
      filelist: verification/unit/core_tb.f
      timeout: 5000

tools:
  sim:
    xsim:
      vlog: xvlog.bat
      xelab: xelab.bat
      bin: xsim.bat
    questa:
      vlog: vlog
      vsim: vsim
    verilator:
      bin: verilator
  
  synth:
    vivado:
      bin: vivado
      tcl: scripts/vivado_synth.tcl
      part: xc7a100tcsg324-1
    yosys:
      bin: yosys
      script: scripts/yosys_synth.ys
      tech: sky130

fw:
  build_dir: .aly_build/fw
  cmake_options:
    - -DCMAKE_BUILD_TYPE=Release
    - -DCMAKE_TOOLCHAIN_FILE=cmake/riscv64-toolchain.cmake
  sources:
    - firmware/src
  includes:
    - firmware/include

mem:
  format: hex
  word_width: 32
  byte_order: little
  start_addr: 0x00000000
''',
            'rtl': {
                'README.md': '''# RTL Sources

SystemVerilog/Verilog HDL sources for the SoC.

## Structure

- `core/` - Processor core (pipeline, ALU, registers)
- `peripherals/` - Memory-mapped peripherals (UART, GPIO, timers)
- `interconnect/` - Bus interconnect (AXI4, APB)
- `soc/` - Top-level SoC integration
- `include/` - Shared RTL headers and packages

## Design Guidelines

1. Use SystemVerilog features (packages, interfaces, assertions)
2. Follow naming convention: `module_name.sv`
3. Add assertions for internal invariants
4. Document interfaces in README files
''',
                'core': {
                    'README.md': '''# Processor Core

Multi-cycle/pipelined RISC-V processor core.

## Modules

- `core.sv` - Top level core integration
- `fetch.sv` - Instruction fetch stage
- `decode.sv` - Instruction decode
- `execute.sv` - Execution stage (ALU)
- `memory.sv` - Memory access stage
- `writeback.sv` - Register writeback

## Features

- RV64I base instruction set
- 5-stage pipeline
- Branch prediction
- CSR support
'''
                },
                'peripherals': {
                    'README.md': '''# Peripherals

Memory-mapped peripheral modules.

## Available Peripherals

- UART - Serial communication
- GPIO - General purpose I/O
- Timer - Programmable timers
- Interrupt Controller
- Memory controller

## Address Map

See `docs/memory_map.md`
'''
                },
                'interconnect': {
                    'README.md': '''# Interconnect

Bus interconnect and bridge modules.

## Components

- AXI4 crossbar
- APB bridge
- Memory router
'''
                },
                'soc': {
                    'README.md': '''# SoC Top

Top-level SoC integration.

## Files

- `soc_top.sv` - Main SoC top module
- `clock_gen.sv` - Clock generation
- `reset_ctrl.sv` - Reset controller
'''
                },
                'include': {
                    'README.md': '''# RTL Includes

Shared packages and headers.

## Files

- `soc_pkg.sv` - SoC-level parameters and types
- `riscv_pkg.sv` - RISC-V definitions
'''
                }
            },
            'firmware': {
                'README.md': '# Firmware\n\nBaremetal firmware for the SoC.',
                'src': {
                    'README.md': '# Source Files\n\nC/Assembly firmware sources.'
                },
                'include': {
                    'README.md': '# Headers\n\nC header files.'
                },
                'linker': {
                    'README.md': '# Linker Scripts\n\nMemory layout definitions.',
                    'link.ld': '''/* Linker script for RISC-V SoC */
OUTPUT_ARCH("riscv")
ENTRY(_start)

MEMORY {
    IMEM : ORIGIN = 0x00000000, LENGTH = 64K
    DMEM : ORIGIN = 0x10000000, LENGTH = 64K
}

SECTIONS {
    .text : {
        *(.text.start)
        *(.text*)
    } > IMEM

    .data : {
        *(.data*)
        *(.rodata*)
    } > DMEM

    .bss : {
        *(.bss*)
        *(COMMON)
    } > DMEM
}
'''
                },
                'startup': {
                    'README.md': '# Startup Code\n\nBootstrap and runtime support.',
                    'crt0.s': '''# Minimal RISC-V startup
.section .text.start
.global _start

_start:
    # Set stack pointer
    la sp, _stack_top
    
    # Clear BSS
    la t0, _bss_start
    la t1, _bss_end
1:
    bge t0, t1, 2f
    sd zero, 0(t0)
    addi t0, t0, 8
    j 1b
2:
    # Call main
    call main
    
    # Hang if main returns
3:
    j 3b
'''
                }
            },
            'verification': {
                'README.md': '# Verification\n\nTestbenches and verification IP.',
                'unit': {
                    'README.md': '# Unit Tests\n\nModule-level testbenches.'
                },
                'integration': {
                    'README.md': '# Integration Tests\n\nSubsystem and SoC-level tests.'
                },
                'tb': {
                    'README.md': '# Testbench Infrastructure\n\nReusable testbench components.'
                }
            },
            'docs': {
                'README.md': '# Documentation\n\nProject documentation and specifications.',
                'architecture.md': '''# Architecture

## Overview

Describe your SoC architecture here.

## Block Diagram

```
[Add block diagram]
```

## Memory Map

| Base Address | Size | Description |
|--------------|------|-------------|
| 0x00000000 | 64KB | Instruction Memory |
| 0x10000000 | 64KB | Data Memory |
''',
                'getting_started.md': '''# Getting Started

## Prerequisites

- RISC-V toolchain (riscv64-unknown-elf-gcc)
- Vivado (for simulation)
- ALY build tool

## Building Firmware

```bash
aly firmware
```

## Running Simulation

```bash
aly simulate
```
'''
            },
            '.gitignore': '''# ALY build outputs
.aly_build/
__pycache__/
*.pyc

# Editor files
.vscode/
.idea/
*.swp
*~

# Vivado
*.jou
*.log
*.pb
xsim.dir/
*.wdb

# Compilation
*.o
*.elf
*.bin
*.lst
*.mem
''',
            'README.md': '''# SoC Project

Created with ALY - Advanced Logic Yieldflow

## Structure

- `rtl/` - RTL sources (SystemVerilog/Verilog)
- `firmware/` - Baremetal C/Assembly firmware
- `verification/` - Testbenches and verification
- `docs/` - Documentation

## Quick Start

```bash
# Build firmware
aly firmware

# Run simulation
aly simulate

# Clean build artifacts
aly clean
```

## Documentation

See [docs/getting_started.md](docs/getting_started.md) for more information.
'''
        }
    },
    'firmware-only': {
        'description': 'Firmware-only project (no RTL)',
        'structure': {
            '.aly': {
                'config': ''
            },
            'src': {},
            'include': {},
            'README.md': '# Firmware Project\n\nCreated with ALY.',
        }
    }
}


class Init(AlyCommand):
    """Initialize a new ALY project."""
    
    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            'init',
            help='initialize a new ALY project',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Initialize a new ALY project from a template.'
        )
        parser.add_argument(
            'path',
            nargs='?',
            default='.',
            help='project directory (default: current directory)'
        )
        parser.add_argument(
            '-t', '--template',
            choices=list(PROJECT_TEMPLATES.keys()),
            default='soc',
            help='project template (default: soc)'
        )
        parser.add_argument(
            '--list-templates',
            action='store_true',
            help='list available templates'
        )
        return parser
    
    def run(self, args, unknown_args):
        if args.list_templates:
            log.banner("Available Templates")
            for name, tmpl in PROJECT_TEMPLATES.items():
                print(f"  {log.Colors.BOLD}{name}{log.Colors.RESET}")
                print(f"    {tmpl['description']}")
            return 0
        
        project_path = Path(args.path).resolve()
        template = PROJECT_TEMPLATES[args.template]
        
        log.banner(f"Initializing ALY Project: {args.template}")
        log.inf(f"Location: {project_path}")
        
        # Check if directory exists and is not empty
        if project_path.exists():
            if any(project_path.iterdir()):
                if (project_path / '.aly').exists():
                    self.die(f"Directory {project_path} is already an ALY project")
                
                self.wrn(f"Directory {project_path} is not empty")
                response = input("Continue? [y/N] ")
                if response.lower() != 'y':
                    log.inf("Cancelled")
                    return 1
        
        # Create directory structure
        project_path.mkdir(parents=True, exist_ok=True)
        self._create_structure(project_path, template['structure'])
        
        log.success(f"Project initialized: {project_path.name}")
        print()
        log.inf("Next steps:")
        print(f"  cd {project_path}")
        print(f"  aly info")
        
        return 0
    
    def _create_structure(self, base_path: Path, structure: dict, indent=0):
        """Recursively create directory structure."""
        for name, content in structure.items():
            path = base_path / name
            
            if isinstance(content, dict):
                # Directory
                path.mkdir(exist_ok=True)
                log.inf(f"  {'  ' * indent}Create dir: {path.relative_to(base_path.parent)}")
                self._create_structure(path, content, indent + 1)
            else:
                # File
                path.write_text(content)
                if content:  # Only log if file has content
                    log.inf(f"  {'  ' * indent}Create file: {path.relative_to(base_path.parent)}")
