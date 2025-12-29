Getting Started
===============

Installation
------------

Install from PyPI:

.. code-block:: bash

   pip install aly

Or install from source:

.. code-block:: bash

   git clone https://github.com/yourusername/aly.git
   cd aly
   pip install -e .

Creating a Project
------------------

List available templates:

.. code-block:: bash

   aly init --list-templates

Create a SoC project:

.. code-block:: bash

   aly init my-soc --template soc
   cd my-soc

This creates:

* ``rtl/`` - HDL sources (core, peripherals, soc)
* ``firmware/`` - C/Assembly firmware
* ``verification/`` - Testbenches
* ``docs/`` - Documentation
* ``.aly/`` - Project configuration

Project Structure
-----------------


The generated project follows a modern, RTL-optimized structure::

    my-soc/
       .aly/                 # ALY project config (YAML, IP, boards)
          config.yaml         # main project config (paths, tools, targets, tests)
          ip.yaml             # IP catalog (optional)
          boards.yaml         # FPGA boards and programming (optional)

       rtl/                  # HDL source code (design only)
          common/             # packages, typedefs, helpers
          ip/                 # each IP core in its own subdir
             core/
             mmu/
             axi/
             usb/
             qspi/
          soc/                # SoC-level integration
          fpga_top/           # FPGA-specific top wrappers (per board)
          asic_top/           # ASIC-specific tops/wrappers (optional)

       tb/                   # All testbench code (no outputs here)
          unit/               # block-level TBs
          soc/                # SoC-level TBs (non-UVM)
          uvm/                # UVM env/tests if used
          models/             # reference models, BFMs, mem models
          constraints/        # sim-only constraints/configs

       fw/                   # Firmware/software for the SoC
          src/
          include/
          linker/
          startup/
          tests/              # SW tests used in regressions

       scripts/              # Helper scripts, called by aly (not by hand)
          sim/                # per-simulator templates/TCL/Python helpers
          synth/              # per-tool TCL/Yosys/Genus scripts
          impl/               # P&R / bitstream generation (FPGA/ASIC)
          prog/               # FPGA programming & debug scripts
          utils/              # shared script helpers

       tools/                # Project-specific utilities, DPI, etc.
          dpi/
          python/             # extra Python modules used by aly if needed

       build/                # ONLY place for generated files (git-ignored)
          sim/                # waves, logs, coverage, per-test dirs
          synth/              # netlists, synth logs, reports
          impl/               # P&R outputs: bitstreams, DEF, GDS, etc.
          fw/                 # compiled firmware: ELF, bin, hex, mem
          ip/                 # generated IP outputs or vendor IP cores
          logs/               # aggregated logs
          test_results/       # regression results, reports
          scratch/            # misc temporary data

       doc/                  # Specs, planning, design & verification docs
          requirements/
          verification/
          architecture/

       README.md
       .gitignore

**Key rules:**

- One output root: all generated artifacts go under build/ (sim, synth, impl, fw, etc.).
- rtl/ is for synthesizable design code only.
- tb/ holds all verification/testbench code (unit, soc, uvm, models).
- scripts/ holds helper scripts per tool/flow, not results.
- .aly/ stores ALY’s project configs (YAML) and optional IP/board catalogs.
- aly is the single front‑door for everything (no Makefile).

Building Firmware
-----------------

Build all firmware:

.. code-block:: bash

   aly firmware

Build specific files:

.. code-block:: bash

   aly firmware firmware/src/main.c firmware/src/startup.asm

Output goes to ``.aly_build/firmware/``:

* ``.elf`` - Executable binary
* ``.bin`` - Raw binary
* ``.mem`` - Verilog hex format
* ``.lst`` - Disassembly listing

Requirements
------------

* Python 3.8 or later
* RISC-V toolchain (``riscv64-unknown-elf-gcc``) for firmware builds
* Vivado (optional, for simulation)

The toolchain must be in your ``PATH``. ALY auto-detects tools.

Check Configuration
-------------------

.. code-block:: bash

   aly info

This shows:

* Project root
* Build directory
* Toolchain status (RISC-V, Vivado)
* Source files found

Next Steps
----------

* Read :doc:`commands` for all available commands
* Learn :doc:`extensions` to add custom commands
* See :doc:`api` for Python API documentation
