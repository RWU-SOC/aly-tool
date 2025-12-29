RTL Workflow Guide
==================

ALY provides a comprehensive RTL design and verification workflow with support for multiple industry-standard EDA tools.

Overview
--------

The RTL workflow includes:

- **Simulation** - Run functional verification with Vivado XSIM, Questa/ModelSim, or Verilator
- **Synthesis** - Synthesize designs with Vivado or Yosys
- **Firmware** - Build RISC-V firmware and convert to memory files
- **Regression** - Automated test suite execution with parallel support

Configuration
-------------

RTL workflows are configured via ``aly_workflow.yaml`` in your project root.

Example Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    project:
      name: my-soc
      version: "1.0.0"

    rtl:
      top: soc_top
      dirs:
        - rtl/core
        - rtl/peripherals
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
      
      synth:
        vivado:
          bin: vivado
          part: xc7a100tcsg324-1

Simulation
----------

Run RTL simulations with pluggable simulator backends.

Basic Usage
~~~~~~~~~~~

.. code-block:: bash

    # Simulate with XSIM (default)
    aly sim --top soc_tb --waves
    
    # Use Questa/ModelSim
    aly sim --top soc_tb --tool questa --waves
    
    # Use Verilator (fast, open-source)
    aly sim --top soc_tb --tool verilator
    
    # Open GUI for debugging
    aly sim --top soc_tb --gui --waves

Simulation Options
~~~~~~~~~~~~~~~~~~

- ``--tool`` - Simulator to use: xsim, questa, modelsim, verilator
- ``--top`` - Top module/testbench name
- ``--waves`` - Enable waveform dumping
- ``--gui`` - Open simulator GUI
- ``--plusargs`` - Pass plusargs to simulator (e.g., ``+verbose +seed=42``)
- ``--timeout`` - Simulation timeout in seconds
- ``--config`` - Path to workflow config (default: aly_workflow.yaml)

Waveform Viewing
~~~~~~~~~~~~~~~~

Waveforms are saved in ``.aly_build/sim/<tool>/<top>/``:

- XSIM: ``<top>.wdb`` (open with Vivado)
- Questa: ``<top>.wlf`` (open with Questa)
- Verilator: ``<top>.vcd`` (open with GTKWave)

Synthesis
---------

Synthesize RTL designs for FPGA or ASIC targets.

Basic Usage
~~~~~~~~~~~

.. code-block:: bash

    # Synthesize with Vivado
    aly synth --tool vivado --top soc_top --part xc7a100tcsg324-1
    
    # Synthesize with Yosys (open-source)
    aly synth --tool yosys --top soc_top --part sky130
    
    # Add timing constraints
    aly synth --tool vivado --top soc_top --constraints timing.xdc
    
    # Show reports
    aly synth --tool vivado --top soc_top --report

Synthesis Options
~~~~~~~~~~~~~~~~~

- ``--tool`` - Synthesis tool: vivado, yosys
- ``--top`` - Top module name
- ``--part`` - FPGA part number or technology library
- ``--constraints`` - Constraint files (XDC for Vivado, SDC for others)
- ``--report`` - Print synthesis reports
- ``--config`` - Path to workflow config

Output Files
~~~~~~~~~~~~

Synthesis outputs are in ``.aly_build/synth/<tool>/<top>/``:

- ``<top>_synth.dcp`` - Vivado design checkpoint
- ``<top>_synth.v`` - Synthesized netlist
- ``reports/`` - Utilization, timing, power, DRC reports

Timing Analysis
~~~~~~~~~~~~~~~

ALY checks timing automatically:

.. code-block:: text

    ✓ Synthesis completed in 45.2s - Timing MET
    
    or
    
    ⚠ Synthesis completed in 45.2s - Timing NOT MET

Firmware and Memory Files
--------------------------

Build firmware and generate memory initialization files.

Build Firmware
~~~~~~~~~~~~~~

.. code-block:: bash

    # Build all firmware
    aly firmware
    
    # Build specific target
    aly firmware --target hello_world
    
    # Clean build
    aly firmware --clean

Generate Memory Files
~~~~~~~~~~~~~~~~~~~~~

Convert ELF binaries to memory initialization formats:

.. code-block:: bash

    # Generate hex file (default)
    aly gen-mem firmware.elf
    
    # Verilog $readmemh format
    aly gen-mem firmware.elf --format mem
    
    # Xilinx COE format
    aly gen-mem firmware.elf --format coe
    
    # Binary format
    aly gen-mem firmware.elf --format bin
    
    # Custom word width and byte order
    aly gen-mem firmware.elf --format hex --word-width 64 --byte-order big
    
    # Pad to specific size
    aly gen-mem firmware.elf --format mem --size 65536

Supported Formats
~~~~~~~~~~~~~~~~~

- ``hex`` - Intel HEX format (plain hex values)
- ``mem`` - Verilog ``$readmemh`` format
- ``bin`` - Raw binary
- ``coe`` - Xilinx COE format for BlockRAM initialization
- ``verilog`` - Verilog array initialization syntax

Regression Testing
------------------

Run automated regression test suites with parallel execution.

Basic Usage
~~~~~~~~~~~

.. code-block:: bash

    # Run all tests
    aly regress --tool xsim
    
    # Run specific test suite
    aly regress --suite smoke --tool questa
    
    # Run specific tests
    aly regress --test core_tb --test uart_tb
    
    # Parallel execution (4 jobs)
    aly regress --tool verilator -j 4
    
    # Capture waveforms for debugging
    aly regress --suite nightly --waves
    
    # Stop on first failure
    aly regress --tool xsim --stop-on-fail

Regression Options
~~~~~~~~~~~~~~~~~~

- ``--tool`` - Simulator to use
- ``--suite`` - Test suite name (defined in config)
- ``--test`` - Specific test(s) to run
- ``-j`` - Number of parallel jobs (default: 1)
- ``--waves`` - Enable waveform capture
- ``--timeout`` - Test timeout in seconds (default: 300)
- ``--stop-on-fail`` - Stop on first failure
- ``--config`` - Path to workflow config

Test Configuration
~~~~~~~~~~~~~~~~~~

Define tests in ``aly_workflow.yaml``:

.. code-block:: yaml

    tb:
      tops:
        core_tb:
          filelist: verification/unit/core_tb.f
          timeout: 5000
          suite: smoke
          plusargs:
            - verbose
            - seed=42
        
        soc_tb:
          filelist: verification/integration/soc_tb.f
          timeout: 10000
          suite: nightly

Regression Output
~~~~~~~~~~~~~~~~~

.. code-block:: text

    ========================================
    Regression: 10 tests
    ========================================
    Tool: xsim
    Parallel jobs: 4
    
    [PASS] core_tb (2.3s)
    [PASS] uart_tb (1.8s)
    [FAIL] spi_tb (3.1s)
    ...
    
    ========================================
    Regression Summary
    ========================================
    Total tests: 10
    Passed: 9
    Failed: 1
    Duration: 25.4s

Advanced Usage
--------------

Multi-Tool Workflows
~~~~~~~~~~~~~~~~~~~~

Run the same tests with different simulators:

.. code-block:: bash

    # Fast verification with Verilator
    aly regress --tool verilator -j 8 --suite smoke
    
    # Full verification with Questa
    aly regress --tool questa --suite nightly

Complete Flow Example
~~~~~~~~~~~~~~~~~~~~~

Typical SoC design workflow:

.. code-block:: bash

    # 1. Initialize project
    aly init my-soc --type soc
    cd my-soc
    
    # 2. Build firmware
    aly firmware
    
    # 3. Generate memory files
    aly gen-mem .aly_build/fw/firmware.elf --format mem
    
    # 4. Run unit tests
    aly regress --suite unit --tool verilator -j 4
    
    # 5. Run integration tests with waveforms
    aly sim --top soc_tb --tool xsim --waves --gui
    
    # 6. Run full regression
    aly regress --suite full --tool questa -j 4
    
    # 7. Synthesize design
    aly synth --tool vivado --top soc_top --report

Continuous Integration
~~~~~~~~~~~~~~~~~~~~~~

Example GitHub Actions workflow:

.. code-block:: yaml

    name: RTL Verification
    on: [push, pull_request]
    
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          
          - name: Install tools
            run: |
              sudo apt-get update
              sudo apt-get install -y verilator
          
          - name: Install ALY
            run: pip install aly
          
          - name: Run regression
            run: aly regress --tool verilator -j 4

Backend Architecture
--------------------

ALY uses a pluggable backend system for extensibility.

Supported Simulators
~~~~~~~~~~~~~~~~~~~~

- **Vivado XSIM** - Free with Vivado, good for Xilinx designs
- **Questa/ModelSim** - Industry standard, advanced debugging
- **Verilator** - Open-source, very fast, C++ based

Supported Synthesis Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Vivado** - Xilinx FPGA synthesis
- **Yosys** - Open-source synthesis for ASIC and FPGA

Adding Custom Backends
~~~~~~~~~~~~~~~~~~~~~~~

Create custom backends by extending base classes:

.. code-block:: python

    from aly.backends import SimulatorBackend, SimulationResult
    
    class MySimBackend(SimulatorBackend):
        def compile(self, sources, top, output_dir, ...):
            # Run your compiler
            pass
        
        def simulate(self, top, output_dir, ...):
            # Run simulation
            return SimulationResult(...)

Register in your extension:

.. code-block:: yaml

    # .aly/commands.yml
    aly-commands:
      - name: sim-custom
        module: my_extension.sim_backend
        class: MySimBackend

Best Practices
--------------

Directory Structure
~~~~~~~~~~~~~~~~~~~

Organize your project following ALY conventions:

.. code-block:: text

    my-soc/
    ├── aly_workflow.yaml      # Workflow configuration
    ├── rtl/                   # RTL sources
    │   ├── core/
    │   ├── peripherals/
    │   └── include/
    ├── verification/          # Testbenches
    │   ├── unit/
    │   ├── integration/
    │   └── lib/               # Reusable components
    ├── firmware/              # Firmware sources
    │   ├── src/
    │   ├── include/
    │   └── linker/
    ├── docs/                  # Documentation
    └── .aly_build/            # Build outputs (gitignored)

Version Control
~~~~~~~~~~~~~~~

Add to ``.gitignore``:

.. code-block:: text

    # ALY build outputs
    .aly_build/
    
    # Simulator outputs
    *.wdb
    *.wlf
    *.vcd
    *.log
    *.jou
    
    # Synthesis outputs
    *.dcp
    vivado*.log

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

- Keep ``aly_workflow.yaml`` in version control
- Use environment-specific configs for different machines
- Document tool paths and versions in README

Waveform Debugging
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Quick functional check - no waves
    aly sim --top core_tb --tool verilator
    
    # Debug with waveforms
    aly sim --top core_tb --tool xsim --waves --gui
    
    # Capture waves for later analysis
    aly sim --top soc_tb --waves
    # Then open .aly_build/sim/xsim/soc_tb/soc_tb.wdb

Performance Tips
~~~~~~~~~~~~~~~~

- Use Verilator for fast regression (10-100x faster)
- Use XSIM/Questa for detailed debugging
- Run regressions in parallel: ``-j 8``
- Use ``--stop-on-fail`` during development
- Disable waves in regression for speed

Troubleshooting
---------------

Simulation Fails to Start
~~~~~~~~~~~~~~~~~~~~~~~~~~

Check tool paths in config:

.. code-block:: bash

    aly info  # Shows tool availability

Timing Not Met
~~~~~~~~~~~~~~

.. code-block:: bash

    # Generate detailed timing report
    aly synth --tool vivado --top soc_top --report
    
    # Check reports/timing_summary.rpt

Compilation Errors
~~~~~~~~~~~~~~~~~~

Check include paths and defines:

.. code-block:: yaml

    rtl:
      includes:
        - rtl/include
        - ip/xilinx/include
      defines:
        SIMULATION: "1"
        DEBUG_LEVEL: "2"

Memory File Issues
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Verify ELF file
    riscv64-unknown-elf-readelf -h firmware.elf
    
    # Check section sizes
    riscv64-unknown-elf-size firmware.elf
    
    # Extract specific section
    aly gen-mem firmware.elf --section .text --format mem

Additional Resources
--------------------

- `ALY GitHub Repository <https://github.com/yourusername/aly>`_
- `Vivado User Guide <https://www.xilinx.com/support/documentation/>`_
- `Questa User Manual <https://www.intel.com/content/www/us/en/docs/>`_
- `Verilator Manual <https://verilator.org/guide/latest/>`_
- `Yosys Manual <https://yosyshq.net/yosys/documentation.html>`_
