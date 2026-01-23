# ALY - Advanced Logic Yieldflow

**Professional Python build and verification tool for RTL/SoC development**


[![Documentation](https://github.com/RWU-SOC/aly-tool/workflows/Build%20and%20Deploy%20Documentation/badge.svg)](https://RWU-SOC.github.io/aly-tool/)
[![PyPI](https://img.shields.io/pypi/v/aly-tool.svg)](https://pypi.org/project/aly-tool/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)

## Features

### RTL Workflow
- **Multi-Tool Simulation** - XSIM, Questa/ModelSim, Verilator, Icarus Verilog
- **Synthesis** - Vivado (FPGA), Yosys (open-source/ASIC)
- **Linting** - Verilator lint, Vivado DRC
- **Waveform Management** - Automated capture and viewing with GTKWave

### Firmware & Memory
- **RISC-V Toolchain** - Integrated firmware builds (RV32/RV64)
- **Memory Generation** - ELF to hex/mem/bin/COE/Verilog conversion

### Developer Experience
- **Project Templates** - Bootstrap complete SoC projects with `aly init`
- **Manifest System** - YAML-based RTL, testbench, and firmware manifests
- **Pluggable Backends** - Clean simulator/synthesis tool abstraction
- **Hierarchical Configuration** - Project-wide settings with per-component overrides

## Quick Start

### Installation

```bash
pip install aly-tool
```

Or install from source:

```bash
git clone https://github.com/RWU-SOC/aly-tool.git
cd aly-tool
pip install -e .
```

### Create a New Project

```bash
# Create new RV64I SoC project (default template)
aly init my-soc
cd my-soc

# Create project with specific template
aly init my-project --template soc

# List available templates
aly init --list-templates

# Pass template variables
aly init my-cpu --var language=verilog --var toolchain=riscv32
```

### RTL Simulation

```bash
# Run simulation with XSIM (Vivado)
aly sim --top soc_tb --tool xsim --waves

# Run with Questa/ModelSim
aly sim --top soc_tb --tool questa --gui

# Run with Verilator (fast)
aly sim --top core_tb --tool verilator

```

### Synthesis

```bash
# Vivado synthesis for FPGA
aly synth --module alu --part xc7a100tcsg324-1

# Yosys synthesis (generic/ASIC)
aly synth --module alu --part xc7a100tcsg324-1 --tool yosys
```

### Linting

```bash
# Lint specific module
aly lint --module cpu_core

# Lint with specific tool
aly lint --module cpu_core --tool slang

# Lint specific files
aly lint rtl/cpu.sv rtl/alu.sv
```

### Build Firmware

```bash
# Build all firmware
aly firmware

# Build specific firmware
aly firmware instr_test

# List available builds
aly firmware --list
```

### Other Commands

```bash
# Show project information
aly info

# Clean build artifacts
aly clean

# Manage constraints
aly constraints list

# Show version
aly version
```

## Project Structure

ALY generates well-organized SoC projects:

```
my-soc/
├── .aly/                  # ALY configuration
│   ├── config.yaml        # Project settings
│   ├── sim.yaml           # Simulation config
│   ├── synth.yaml         # Synthesis config
│   ├── lint.yaml          # Linting config
│   ├── toolchains.yaml    # Toolchain paths
│   └── constraints.yaml   # Constraint sets
├── rtl/                   # HDL sources
│   ├── pkg/               # SystemVerilog packages
│   ├── core/              # Processor core
│   │   ├── alu/
│   │   ├── decoder/
│   │   └── regfile/
│   ├── bus/               # Bus interfaces
│   ├── mem/               # Memory modules
│   └── soc_top/           # Top-level integration
├── tb/                    # Testbenches
│   ├── unit/              # Module tests
│   └── integration/       # System tests
├── fw/                    # Firmware
│   └── instr_test/        # Test programs
├── ip/                    # External IP
├── synth/                 # Synthesis files
│   └── constraints/       # XDC/SDC constraints
├── docs/                  # Documentation
└── build/                 # Build outputs (gitignored)
```

## Manifest System

ALY uses YAML manifests to describe RTL modules, testbenches, and firmware:

### RTL Manifest (`rtl/core/manifest.yaml`)

```yaml
name: cpu_core
version: 1.0.0
type: rtl
language: systemverilog

modules:
  - name: cpu_core
    top: cpu_core
    files:
      - CPU.sv
      - PC.sv
    dependencies:
      - name: cpu_pkg
        type: package
      - name: cpu_alu
        type: rtl
```

### Testbench Manifest (`tb/unit/manifest.yaml`)

```yaml
name: unit_tests
type: testbench
version: 1.0.0

testbenches:
  - name: tb_alu
    top: tb_alu
    files:
      - tb_alu.sv
    dependencies:
      - name: cpu_alu
        type: rtl

testsuites:
  - name: unit_tests
    testbenches: [tb_alu, tb_regfile]
    parallel: 4
```

### Firmware Manifest (`fw/instr_test/manifest.yaml`)

```yaml
name: instr_test
type: firmware
toolchain: riscv64

builds:
  - name: test_program
    languages: [asm]
    sources: [test.asm]
    linker_script: linkers/memory.ld
    outputs:
      - format: elf
      - format: mem
        plusarg: MEM_FILE
```

## Template System

Create custom project templates:

```yaml
# template.yaml
name: my_template
version: "1.0"
description: "Custom SoC template"
extends: base

variables:
  project_name:
    description: "Project name"
    default: "my_project"
  language:
    description: "HDL language"
    choices: [systemverilog, verilog]

structure:
  directories:
    - rtl
    - tb
    - fw

files:
  - src: "rtl/**/*"
    dest: "rtl/"
  - src: "config.yaml.j2"
    dest: ".aly/config.yaml"
    template: true
```

Use Jinja2 templating in `.j2` files:

```jinja
{% if language == 'systemverilog' %}
import {{ project_name }}_pkg::*;
{% endif %}

module {{ project_name }}_top (
    input logic clk_i,
    input logic rst_i
);
endmodule
```

## Documentation

Full documentation available at [RWU-SOC.github.io/aly-tool](https://RWU-SOC.github.io/aly-tool/)

- [Getting Started](https://RWU-SOC.github.io/aly-tool/quickstart.html)
- [Configuration](https://RWU-SOC.github.io/aly-tool/configuration.html)
- [Template System](https://RWU-SOC.github.io/aly-tool/templates.html)
- [Command Reference](https://RWU-SOC.github.io/aly-tool/commands/index.html)
- [API Documentation](https://RWU-SOC.github.io/aly-tool/api/index.html)

## Development

### Setup Development Environment

```bash
git clone https://github.com/RWU-SOC/aly-tool.git
cd aly-tool
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aly

# Run specific test
pytest tests/test_init.py -v
```

### Build Documentation

```bash
cd docs
pip install -r requirements.txt
make html
# View at docs/build/html/index.html
```

## Requirements

- Python 3.8+
- Optional: RISC-V toolchain (`riscv64-unknown-elf-gcc`) for firmware builds
- Optional: Vivado for XSIM simulation and FPGA synthesis
- Optional: Verilator for fast simulation
- Optional: Yosys for open-source synthesis

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Acknowledgments

- Built with Python and Jinja2
- Inspired by modern build systems like Bazel and Buck
