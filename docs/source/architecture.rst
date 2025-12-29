Architecture & Implementation
==============================

This document describes the internal architecture and implementation details of ALY.

System Architecture
-------------------

ALY follows a modular, layered architecture with clear separation of concerns:

.. code-block:: text

    ┌─────────────────────────────────────────┐
    │         CLI Layer (main.py)             │
    │    Command-line parsing & dispatch      │
    └─────────────┬───────────────────────────┘
                  │
    ┌─────────────▼───────────────────────────┐
    │    Command Layer (app/*.py)             │
    │  Built-in & extension commands          │
    └─────────────┬───────────────────────────┘
                  │
    ┌─────────────▼───────────────────────────┐
    │   Backend Layer (backends.py)           │
    │  Abstract interfaces for tools          │
    └─────────────┬───────────────────────────┘
                  │
    ┌─────────────▼───────────────────────────┐
    │  Tool Implementation (sim_*, synth_*)   │
    │  Concrete simulator/synthesis backends  │
    └─────────────────────────────────────────┘

Core Components
---------------

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

**File:** ``configuration.py`` (90 lines)

Hierarchical configuration system:

1. System-wide: ``~/.alyconfig``
2. Project-level: ``.aly/config``
3. Environment variables: ``ALY_*``
4. Command-line arguments

Configuration is loaded lazily and cached for performance.

**File:** ``workflow_config.py`` (130 lines)

YAML-based workflow configuration for RTL/verification:

- ``WorkflowConfig`` - Main configuration class
- ``RTLConfig`` - RTL sources, includes, defines
- ``TestbenchConfig`` - Testbench configurations
- ``ToolConfig`` - Tool-specific settings

Extension System
~~~~~~~~~~~~~~~~

**File:** ``commands.py`` (200 lines)

West-style extension system allowing custom commands:

- Discovers ``.aly/commands.yml`` in project
- Dynamically loads Python modules
- Caches loaded extensions for performance
- Supports multiple command files

Extension discovery order:

1. Built-in commands (always available)
2. Project commands (``.aly/commands.yml``)
3. Custom paths (``aly.commands-path`` config)
4. Environment overrides (``ALY_COMMANDS_PATH``)

Backend Architecture
~~~~~~~~~~~~~~~~~~~~

**File:** ``backends.py`` (150 lines)

Abstract base classes for pluggable tool backends:

- ``SimulatorBackend`` - Abstract interface for simulators
- ``SynthesisBackend`` - Abstract interface for synthesis tools
- ``SimulationResult`` - Dataclass for simulation results
- ``SynthesisResult`` - Dataclass for synthesis results

Design pattern: Abstract Base Class (ABC) with ``@abstractmethod``

Logging System
~~~~~~~~~~~~~~

**File:** ``log.py`` (60 lines)

Colored, hierarchical logging:

- ``banner()`` - Section headers
- ``inf()`` - Information messages
- ``wrn()`` - Warnings
- ``err()`` - Errors
- ``dbg()`` - Debug messages
- ``success()`` - Success messages

Verbosity levels:

- Normal: Info, warnings, errors
- Verbose (``-v``): + Debug messages
- Very verbose (``-vv``): + Tool output
- Quiet (``-q``): Errors only

Utilities
~~~~~~~~~

**File:** ``util.py`` (50 lines)

Helper functions:

- ``find_tool()`` - Search PATH for executables
- ``find_aly_root()`` - Find project root (``.aly`` directory)
- ``run_command()`` - Execute subprocess with logging
- ``validate_toolchain()`` - Check tool availability

RTL Workflow Implementation
----------------------------

Simulator Backends
~~~~~~~~~~~~~~~~~~

**XSIM Backend** (``sim_xsim.py``, 170 lines)

Vivado XSIM simulator integration:

- Compilation: ``xvlog`` with SystemVerilog support
- Elaboration: ``xelab`` with debug information
- Simulation: ``xsim`` with waveform dumping
- Waveform format: ``.wdb`` (Vivado waveform database)
- GUI mode: Interactive debugging support

**Questa Backend** (``sim_questa.py``, 200 lines)

Questa/ModelSim simulator integration:

- Work library management: ``vlib``
- Compilation: ``vlog`` with lint checks
- Simulation: ``vsim`` in batch or GUI mode
- Waveform format: ``.wlf`` (Questa waveform log)
- Advanced features: Coverage, assertions

**Verilator Backend** (``sim_verilator.py``, 200 lines)

Verilator open-source simulator:

- Compilation: Verilate to C++
- Execution: Run compiled C++ executable
- Waveform format: ``.vcd`` (VCD standard)
- Performance: 10-100x faster than event simulators
- Testbench: C++ based

Synthesis Backends
~~~~~~~~~~~~~~~~~~

**Vivado Backend** (``synth_vivado.py``, 200 lines)

Xilinx Vivado FPGA synthesis:

- TCL script generation for automation
- Batch mode execution
- Timing analysis and closure checking
- Reports: Utilization, timing, power, DRC
- Output: DCP checkpoints, netlists

**Yosys Backend** (``synth_yosys.py``, 180 lines)

Yosys open-source synthesis:

- Script-based synthesis flow
- Technology mapping (generic, sky130, ice40, ecp5)
- Statistics extraction
- Output: Verilog/JSON netlists

Memory Generation
~~~~~~~~~~~~~~~~~

**File:** ``gen_mem.py`` (220 lines)

ELF to memory file conversion:

- Uses ``objcopy`` for binary extraction
- Supports multiple output formats
- Configurable word width and byte order
- Memory padding and sizing

Formats:

- **hex**: Plain hex values (one word per line)
- **mem**: Verilog ``$readmemh`` format
- **bin**: Raw binary
- **coe**: Xilinx COE for block RAM initialization
- **verilog**: Verilog array initialization syntax

Regression Testing
~~~~~~~~~~~~~~~~~~

**File:** ``regress.py`` (320 lines)

Automated test suite execution:

- Test discovery from YAML configuration
- Parallel execution using ThreadPoolExecutor
- Per-test timeout and plusargs
- Pass/fail tracking and reporting
- Suite-based organization

Test workflow:

1. Load configuration (``aly_workflow.yaml``)
2. Filter tests by suite/name
3. Compile + elaborate + simulate for each test
4. Collect results and generate summary
5. Return non-zero exit code if any test fails

Command Implementation
----------------------

Built-in Commands
~~~~~~~~~~~~~~~~~

All commands inherit from ``AlyCommand`` base class:

.. code-block:: python

    class AlyCommand(abc.ABC):
        @staticmethod
        @abstractmethod
        def add_parser(parser_adder):
            """Add command-specific arguments."""
            pass
        
        @abstractmethod
        def run(self, args, unknown_args):
            """Execute the command."""
            pass

**Init Command** (``init.py``, 180 lines)

Project initialization:

- Template selection (soc, firmware-only)
- Directory structure generation
- Starter files (crt0.s, link.ld, README.md)
- Configuration setup

**Firmware Command** (``firmware.py``, 220 lines)

Firmware build automation:

- CMake integration
- RISC-V toolchain detection
- Build directory management
- Progress reporting

**Simulate Command** (``simulate.py``, 154 lines)

RTL simulation:

- Backend selection (xsim, questa, verilator)
- Source file collection
- Compile → elaborate → simulate workflow
- Waveform and log management

**Synthesize Command** (``synthesize.py``, 180 lines)

RTL synthesis:

- Backend selection (vivado, yosys)
- Constraint file handling
- Timing analysis
- Report generation

Data Flow
---------

Simulation Flow
~~~~~~~~~~~~~~~

.. code-block:: text

    User Command
        │
        ▼
    Load Configuration (aly_workflow.yaml)
        │
        ▼
    Collect RTL Sources (from config.rtl.dirs)
        │
        ▼
    Select Backend (based on --tool)
        │
        ▼
    Compile Phase
    ├─ xvlog (XSIM)
    ├─ vlog (Questa)
    └─ verilator (Verilator)
        │
        ▼
    Elaborate Phase
    ├─ xelab (XSIM)
    ├─ (vsim does this) (Questa)
    └─ (compile does this) (Verilator)
        │
        ▼
    Simulate Phase
    ├─ xsim (XSIM)
    ├─ vsim (Questa)
    └─ ./Vtop (Verilator)
        │
        ▼
    Collect Results
    ├─ Log files
    ├─ Waveforms (.wdb/.wlf/.vcd)
    └─ Return status

Synthesis Flow
~~~~~~~~~~~~~~

.. code-block:: text

    User Command
        │
        ▼
    Load Configuration
        │
        ▼
    Collect RTL Sources
        │
        ▼
    Select Backend
        │
        ▼
    Generate Script (TCL/Yosys)
        │
        ▼
    Run Tool in Batch Mode
    ├─ vivado -mode batch -source synth.tcl
    └─ yosys -s synth.ys
        │
        ▼
    Check Timing (if Vivado)
        │
        ▼
    Generate Reports
        │
        ▼
    Return Results

Extension Loading
~~~~~~~~~~~~~~~~~

.. code-block:: text

    Startup
        │
        ▼
    Load Built-in Commands
        │
        ▼
    Find Project Root (.aly/)
        │
        ▼
    Load .aly/commands.yml
        │
        ▼
    Parse Extension Definitions
        │
        ▼
    Import Python Modules
        │
        ▼
    Instantiate Command Classes
        │
        ▼
    Register with Argument Parser
        │
        ▼
    Ready for Dispatch

File Organization
-----------------

Source Layout
~~~~~~~~~~~~~

.. code-block:: text

    src/aly/
    ├── __init__.py              # Package initialization
    ├── __main__.py              # python -m aly entry point
    ├── commands.py              # Extension system
    ├── configuration.py         # Config management
    ├── log.py                   # Logging utilities
    ├── util.py                  # Helper functions
    ├── workflow_config.py       # RTL workflow config
    ├── backends.py              # Abstract backends
    ├── sim_xsim.py             # XSIM backend
    ├── sim_questa.py           # Questa backend
    ├── sim_verilator.py        # Verilator backend
    ├── synth_vivado.py         # Vivado backend
    ├── synth_yosys.py          # Yosys backend
    └── app/
        ├── __init__.py          # Command registry
        ├── firmware.py          # Firmware command
        ├── init.py              # Init command
        ├── simulate.py          # Simulate command
        ├── synthesize.py        # Synthesize command
        ├── gen_mem.py           # Memory gen command
        └── regress.py           # Regression command

Build Outputs
~~~~~~~~~~~~~

.. code-block:: text

    .aly_build/
    ├── sim/
    │   ├── xsim/
    │   │   └── <top>/
    │   │       ├── xsim.dir/        # Compiled design
    │   │       ├── <top>.wdb        # Waveform
    │   │       └── <top>_sim.log    # Simulation log
    │   ├── questa/
    │   └── verilator/
    ├── synth/
    │   ├── vivado/
    │   │   └── <top>/
    │   │       ├── synth.tcl        # Generated script
    │   │       ├── <top>_synth.dcp  # Checkpoint
    │   │       ├── <top>_synth.v    # Netlist
    │   │       └── reports/         # Timing, util, etc.
    │   └── yosys/
    ├── fw/
    │   └── firmware.elf
    └── regress/
        └── <tool>/
            └── <test>/

Performance Considerations
--------------------------

Lazy Loading
~~~~~~~~~~~~

- Configuration files loaded only when needed
- Extensions imported only when used
- Tool executables searched once and cached

Parallel Execution
~~~~~~~~~~~~~~~~~~

Regression testing uses ThreadPoolExecutor:

- Configurable job count (``-j`` flag)
- Thread-safe result collection
- Graceful error handling per test
- Optional stop-on-fail for fast feedback

Memory Management
~~~~~~~~~~~~~~~~~

- Log files written incrementally
- Large tool outputs streamed to files
- Subprocess stdout/stderr captured efficiently
- Temporary files cleaned up after use

Error Handling Strategy
-----------------------

Layered Error Handling
~~~~~~~~~~~~~~~~~~~~~~

1. **Tool Level**: Subprocess returncode checking
2. **Backend Level**: Validate outputs, parse logs
3. **Command Level**: User-friendly error messages
4. **CLI Level**: Exit codes and error display

Error Types
~~~~~~~~~~~

- **ConfigurationError**: Invalid configuration
- **ToolNotFoundError**: Missing executables
- **CompilationError**: RTL compilation failure
- **SimulationError**: Simulation runtime error
- **TimingError**: Timing constraints not met

Testing Strategy
----------------

Unit Tests
~~~~~~~~~~

- Test individual functions in isolation
- Mock external dependencies (tools, filesystem)
- Fast execution (< 1 second per test)
- High coverage of utility functions

Integration Tests
~~~~~~~~~~~~~~~~~

- Test full command workflows
- Use temporary project fixtures
- Verify file generation and structure
- Check command exit codes

Fixtures
~~~~~~~~

- ``temp_project``: Temporary ALY project
- ``mock_toolchain``: Mock tool availability
- ``sample_config``: Pre-configured settings

Future Enhancements
-------------------

Planned Features
~~~~~~~~~~~~~~~~

1. **Additional Simulators**: Xcelium, VCS
2. **Additional Synthesis**: Genus, Design Compiler
3. **Coverage Collection**: Unified coverage reporting
4. **Formal Verification**: Integration with formal tools
5. **Cloud Simulation**: Distributed test execution
6. **GUI**: Web-based regression dashboard
7. **Language Server**: IDE integration

Architecture Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Plugin System**: More dynamic plugin loading
2. **Async I/O**: Non-blocking tool execution
3. **Database Backend**: Result storage and querying
4. **REST API**: Remote command execution

Contributing to Architecture
-----------------------------

When adding new features:

1. Follow existing patterns (ABC for backends)
2. Add comprehensive docstrings
3. Include type hints
4. Write tests for new code
5. Update this documentation
6. Consider backward compatibility

See :doc:`contributing` for detailed guidelines.
