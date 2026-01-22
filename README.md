# 🚀 ALY - Advanced Logic Yieldflow

**Professional Python build and verification tool for RTL/SoC development**

[![Tests](https://github.com/yourusername/aly/workflows/Tests/badge.svg)](https://github.com/yourusername/aly/actions)
[![Documentation](https://readthedocs.org/projects/aly/badge/?version=latest)](https://aly.readthedocs.io)
[![PyPI](https://img.shields.io/pypi/v/aly.svg)](https://pypi.org/project/aly/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)

## Features

### RTL Workflow
- 🎯 **Multi-Tool Simulation** - XSIM, Questa/ModelSim, Verilator
- ⚡ **Synthesis** - Vivado (FPGA), Yosys (open-source)
- 🧪 **Regression Testing** - Parallel test execution
- 📊 **Waveform Management** - Automated capture and viewing

### Firmware & Memory
- 🔧 **RISC-V Toolchain** - CMake-based firmware builds
- 💾 **Memory Generation** - ELF → hex/mem/bin/COE/Verilog

### Developer Experience
- 🏗️ **Project Templates** - Bootstrap complete SoC projects
- 🔌 **Extension System** - Custom commands and backends
- 📦 **Pluggable Backends** - Clean simulator/synthesis abstraction
- ⚙️ **YAML Configuration** - Human-readable workflow config

## Quick Start

### Installation

```bash
pip install aly
```

Or install from source:

```bash
git clone https://github.com/yourusername/aly.git
cd aly
pip install -e .
```

### Create a New Project

```bash
# Create new SoC project
aly init my-soc --type soc
cd my-soc
```

### RTL Simulation

```bash
# Run with XSIM (Vivado)
aly sim --top soc_tb --tool xsim --waves

# Run with Questa/ModelSim
aly sim --top soc_tb --tool questa --gui

# Run with Verilator (fast)
aly sim --top core_tb --tool verilator
```

### Synthesis

```bash
# Vivado synthesis
aly synth --tool vivado --top soc_top --part xc7a100tcsg324-1

# Yosys synthesis
aly synth --tool yosys --top soc_top
```

### Build Firmware

```bash
# Build all firmware
aly firmware

# Generate memory files
aly firmware --mem-format mem  # Memory files generated automatically
```

### Regression Testing

```bash
# Run all tests
aly regress --tool verilator -j 8

# Run specific suite
aly regress --suite smoke --tool xsim
```

### Other Commands

```bash
# Show configuration
aly info

# Clean build artifacts
aly clean

# Show version
aly version
```

## Project Structure

ALY generates well-organized SoC projects:

```
my-soc/
├── .aly/                  # ALY configuration
│   ├── config            # Project settings
│   └── commands.yml      # Custom commands
├── rtl/                   # HDL sources
│   ├── core/             # Processor core
│   ├── peripherals/      # Memory-mapped peripherals
│   └── soc/              # Top-level integration
├── firmware/              # Baremetal software
│   ├── src/              # C/Assembly sources
│   ├── include/          # Headers
│   ├── startup/          # crt0.s
│   └── linker/           # link.ld
├── verification/          # Testbenches
│   ├── unit/             # Module tests
│   ├── integration/      # System tests
│   └── tb/               # Testbench infrastructure
├── docs/                  # Documentation
└── build/                # Build outputs (disposable)
```

## Extension Commands

Add custom commands to your project:

```yaml
# .aly/commands.yml
aly-commands:
  - file: scripts/my_commands.py
    commands:
      - name: simulate
        class: Simulate
        help: run RTL simulation
```

```python
# scripts/my_commands.py
from aly.commands import AlyCommand

class Simulate(AlyCommand):
    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser('simulate', help='run RTL simulation')
        return parser
    
    def run(self, args, unknown_args):
        self.inf("Running simulation...")
        # Your simulation logic here
        return 0
```

## Documentation

Full documentation available at [aly.readthedocs.io](https://aly.readthedocs.io)

- [Getting Started](https://aly.readthedocs.io/getting-started)
- [Command Reference](https://aly.readthedocs.io/commands)
- [Extension Development](https://aly.readthedocs.io/extensions)
- [API Documentation](https://aly.readthedocs.io/api)

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/aly.git
cd aly
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_commands.py

# Run with verbose output
pytest -v

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# View HTML coverage report
# Reports are generated in build/test_results/htmlcov/
python -m http.server --directory build/test_results/htmlcov 8000
```

### Build Documentation

```bash
cd docs
make html
# View at docs/build/html/index.html
```

## Requirements

- Python 3.8+
- RISC-V toolchain (riscv64-unknown-elf-gcc) for firmware builds
- Vivado (optional, for simulation)

## License

Apache License 2.0

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.
