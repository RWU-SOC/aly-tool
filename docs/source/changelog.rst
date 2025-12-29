Changelog
=========

All notable changes to ALY are documented here.

This project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

Version 1.0.0 (2025-01-XX)
--------------------------

Initial Release
~~~~~~~~~~~~~~~

RTL Workflow
^^^^^^^^^^^^

Added comprehensive RTL design and verification workflow:

* **Multi-tool simulation** - Support for Vivado XSIM, Questa/ModelSim, and Verilator
* **Synthesis** - Integration with Vivado (FPGA) and Yosys (open-source)
* **Regression testing** - Automated test suite execution with parallel support (``-j`` flag)
* **Memory file generation** - Convert ELF to hex, mem, bin, COE, and Verilog formats
* **Waveform management** - Automatic waveform capture and viewing

Commands Added
^^^^^^^^^^^^^^

* ``aly sim`` - Run RTL simulation with pluggable backends
* ``aly synth`` - Synthesize RTL designs
* ``aly gen-mem`` - Generate memory initialization files from ELF
* ``aly regress`` - Run automated regression test suites
* ``aly init`` - Initialize projects from templates (SoC, firmware-only)
* ``aly firmware`` - Build RISC-V firmware
* ``aly info`` - Display configuration and toolchain status
* ``aly clean`` - Remove build artifacts
* ``aly version`` - Show version information

Architecture
^^^^^^^^^^^^

* **Pluggable backends** - Abstract base classes for simulator and synthesis tools
* **Extension system** - Custom commands via ``.aly/commands.yml``
* **YAML configuration** - Workflow configuration in ``aly_workflow.yaml``
* **Project templates** - Bootstrap complete SoC projects

Infrastructure
^^^^^^^^^^^^^^

* Comprehensive Sphinx documentation
* GitHub Actions CI/CD workflows (test, release, docs)
* Pytest test suite with fixtures
* Type hints throughout codebase
* Professional package structure

Supported Tools
^^^^^^^^^^^^^^^

Simulators:
  * Vivado XSIM
  * Questa/ModelSim
  * Verilator

Synthesis:
  * Vivado
  * Yosys

Memory Formats:
  * Intel HEX
  * Verilog $readmemh
  * Raw binary
  * Xilinx COE
  * Verilog array initialization
