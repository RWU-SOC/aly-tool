=================
Command Reference
=================

ALY provides a comprehensive CLI for all HDL development tasks.

.. contents::
   :local:
   :depth: 2

Command Overview
----------------

.. graphviz::
   :align: center
   :caption: CLI Command Structure

   digraph commands {
      rankdir=TB;
      node [shape=box, style="rounded,filled", fontname="sans-serif"];

      aly [label="aly", fillcolor="#e3f2fd"];

      init [label="init", fillcolor="#e8f5e9"];
      sim [label="sim", fillcolor="#fff3e0"];
      synth [label="synth", fillcolor="#f3e5f5"];
      lint [label="lint", fillcolor="#fce4ec"];
      fw [label="firmware", fillcolor="#e0f7fa"];
      prog [label="program", fillcolor="#fff8e1"];
      config [label="config", fillcolor="#eceff1"];
      rtl [label="rtl", fillcolor="#e8f5e9"];
      ip [label="ip", fillcolor="#e0f7fa"];

      aly -> init;
      aly -> sim;
      aly -> synth;
      aly -> lint;
      aly -> fw;
      aly -> prog;
      aly -> config;
      aly -> rtl;
      aly -> ip;
   }


Global Options
--------------

These options are available for all commands:

.. code-block:: text

   --help, -h          Show help message and exit

Use ``aly --help`` or ``aly <command> --help`` for detailed command options.


init
----

Initialize a new ALY project.

**Usage:**

.. code-block:: bash

   aly init [OPTIONS] [PATH]

**Arguments:**

.. list-table::
   :widths: 30 70

   * - ``PATH``
     - Directory to create project in (default: current directory)

**Options:**

.. list-table::
   :widths: 30 70

   * - ``-t, --template``
     - Template to use
   * - ``--toolchain``
     - Default firmware toolchain
   * - ``--list-templates``
     - List available templates
   * - ``--no-git``
     - Skip git initialization

**Examples:**

.. code-block:: bash

   # Create project in current directory
   aly init

   # Create project in specified directory
   aly init my_project

   # Use specific template
   aly init my_soc -t rv64i

   # List available templates
   aly init --list-templates


sim
---

Run RTL simulation.

**Usage:**

.. code-block:: bash

   aly sim [OPTIONS]

**Options:**

.. list-table::
   :widths: 30 70

   * - ``--tool``
     - Simulator to use (xsim, verilator, questa, modelsim, iverilog)
   * - ``--top``
     - Top-level testbench module
   * - ``--waves``
     - Enable waveform dumping
   * - ``--gui``
     - Open simulator GUI
   * - ``--plusargs``
     - Pass plusarg to simulator (KEY=VALUE format)
   * - ``--timeout``
     - Simulation timeout
   * - ``--show-log``
     - Display simulation log output
   * - ``--gtkwave``
     - Launch GTKWave after simulation
   * - ``--regress``
     - Run all tests in regression mode
   * - ``--suite``
     - Run a specific test suite
   * - ``--test``
     - Run a specific testbench by name
   * - ``-j, --jobs``
     - Number of parallel jobs (default: 1)
   * - ``--stop-on-fail``
     - Stop on first test failure
   * - ``--list``
     - List available testbenches
   * - ``--list-tags``
     - List tests by tag
   * - ``--list-suites``
     - List test suites

**Examples:**

.. code-block:: bash

   # Basic simulation
   aly sim --top tb_counter

   # With waveforms using Verilator
   aly sim --top tb_alu --tool verilator --waves

   # Run test suite
   aly sim --suite regression

   # Run all tests in parallel
   aly sim --regress -j 4

   # With plusargs
   aly sim --top tb_cpu --plusargs FIRMWARE=boot.hex

   # List available tests
   aly sim --list

.. uml::
   :align: center
   :caption: Simulation Flow

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   start
   :Parse manifest;
   :Resolve dependencies;
   :Compile RTL sources;
   :Compile testbench;
   :Elaborate design;
   :Run simulation;

   if (Waves enabled?) then (yes)
     :Dump waveforms;
   endif

   :Report results;
   stop
   @enduml


synth
-----

Synthesize design for FPGA or ASIC.

**Usage:**

.. code-block:: bash

   aly synth [OPTIONS]

**Options:**

.. list-table::
   :widths: 30 70

   * - ``--module``
     - RTL module to synthesize
   * - ``--tool``
     - Synthesis tool (vivado, yosys)
   * - ``--top``
     - Top-level module name
   * - ``--part``
     - FPGA part number
   * - ``--constraints``
     - Constraint files
   * - ``-j, --jobs``
     - Number of parallel jobs
   * - ``--report``
     - Generate synthesis reports

**Examples:**

.. code-block:: bash

   # Synthesize with default tool
   aly synth --module cpu_core --top cpu_top

   # Synthesize for specific FPGA
   aly synth --tool vivado --part xc7a100tcsg324-1

   # Use Yosys for ASIC
   aly synth --tool yosys --top my_design

   # Generate reports
   aly synth --module cpu_core --report


lint
----

Run linting and static analysis.

**Usage:**

.. code-block:: bash

   aly lint [OPTIONS] [FILES...]

**Arguments:**

.. list-table::
   :widths: 30 70

   * - ``FILES``
     - Specific files to lint (optional)

**Options:**

.. list-table::
   :widths: 30 70

   * - ``--tool``
     - Linter to use (verilator, slang)
   * - ``-m, --module``
     - Lint specific module only
   * - ``--top``
     - Top-level module name
   * - ``--no-warnings``
     - Suppress warnings (errors only)

**Examples:**

.. code-block:: bash

   # Lint all RTL
   aly lint

   # Lint specific module
   aly lint -m alu

   # Lint specific files
   aly lint rtl/cpu.sv rtl/alu.sv

   # Errors only (no warnings)
   aly lint --no-warnings


firmware
--------

Build embedded firmware.

**Usage:**

.. code-block:: bash

   aly firmware [BUILD_NAME] [OPTIONS]

**Arguments:**

.. list-table::
   :widths: 30 70

   * - ``BUILD_NAME``
     - Firmware build name from manifest (optional)

**Options:**

.. list-table::
   :widths: 30 70

   * - ``-o, --output``
     - Output directory
   * - ``--toolchain``
     - Override toolchain
   * - ``--no-mem``
     - Skip memory file generation
   * - ``--mem-format``
     - Memory file format (mem, hex, coe)
   * - ``--word-width``
     - Memory word width (8, 16, 32, 64)
   * - ``--byte-order``
     - Byte order (little, big)
   * - ``--list``
     - List available builds

**Examples:**

.. code-block:: bash

   # Build all firmware
   aly firmware

   # Build specific target
   aly firmware bootloader

   # Build with specific output directory
   aly firmware bootloader -o build/fw

   # List available builds
   aly firmware --list

   # Build with custom memory format
   aly firmware bootloader --mem-format hex --word-width 32


program
-------

Program FPGA device.

**Usage:**

.. code-block:: bash

   aly program [OPTIONS]

**Options:**

.. list-table::
   :widths: 30 70

   * - ``-l, --list``
     - List available programming targets
   * - ``-t, --target``
     - Target board/device name
   * - ``-b, --bitstream``
     - Path to bitstream file
   * - ``--tool``
     - Programming tool (vivado, openocd)
   * - ``-f, --flash``
     - Program to flash memory
   * - ``-v, --verify``
     - Verify after programming

**Examples:**

.. code-block:: bash

   # Program default board
   aly program

   # Specific bitstream
   aly program -b build/synth/fpga_top.bit

   # Program to flash
   aly program -b bitstream.bit --flash

   # List available targets
   aly program --list


config
------

Manage project configuration.

**Usage:**

.. code-block:: bash

   aly config [SUBCOMMAND] [OPTIONS]

**Subcommands:**

.. list-table::
   :widths: 20 80

   * - ``show``
     - Display current configuration
   * - ``validate``
     - Validate configuration files
   * - ``get``
     - Get specific config value
   * - ``set``
     - Set config value
   * - ``edit``
     - Open config file in editor
   * - ``init``
     - Initialize config file
   * - ``list``
     - List config files

**Examples:**

.. code-block:: bash

   # Show all config
   aly config show

   # Validate config
   aly config validate

   # Get specific value
   aly config get defaults.simulator

   # Set value
   aly config set defaults.simulator verilator

   # Edit config file
   aly config edit

   # List config files
   aly config list


rtl
---

RTL management commands.

**Usage:**

.. code-block:: bash

   aly rtl [SUBCOMMAND] [OPTIONS]

**Subcommands:**

.. list-table::
   :widths: 20 80

   * - ``init``
     - Initialize RTL manifest
   * - ``add``
     - Add files to module
   * - ``list``
     - List RTL modules
   * - ``show``
     - Show module details
   * - ``packages``
     - List package files

**Examples:**

.. code-block:: bash

   # Initialize RTL manifest
   aly rtl init

   # List all modules
   aly rtl list

   # Show module details
   aly rtl show cpu_core

   # Add files to module
   aly rtl add --module cpu_core rtl/cpu/*.sv

   # List packages
   aly rtl packages


ip
--

IP block management.

**Usage:**

.. code-block:: bash

   aly ip [SUBCOMMAND] [OPTIONS]

**Subcommands:**

.. list-table::
   :widths: 20 80

   * - ``init``
     - Initialize IP manifest
   * - ``list``
     - List available IP blocks
   * - ``show``
     - Show IP details
   * - ``add``
     - Add IP to project
   * - ``remove``
     - Remove IP from project
   * - ``create``
     - Create new IP block
   * - ``package``
     - Package IP for distribution
   * - ``update``
     - Update IP version

**Examples:**

.. code-block:: bash

   # List available IP
   aly ip list

   # Show IP details
   aly ip show uart

   # Create new IP block
   aly ip create my_uart

   # Add existing IP
   aly ip add vendor/uart

   # Package IP
   aly ip package uart


constraints
-----------

Manage design constraints.

**Usage:**

.. code-block:: bash

   aly constraints [SUBCOMMAND] [OPTIONS]

**Subcommands:**

.. list-table::
   :widths: 20 80

   * - ``init``
     - Initialize constraints configuration
   * - ``list``
     - List constraint sets
   * - ``show``
     - Show constraint set details
   * - ``validate``
     - Validate constraint files

**Examples:**

.. code-block:: bash

   # List constraint sets
   aly constraints list

   # Show specific constraint set
   aly constraints show arty_a7

   # Validate constraints
   aly constraints validate


Exit Codes
----------

ALY uses standard exit codes:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Code
     - Meaning
   * - 0
     - Success
   * - 1
     - General error
   * - 2
     - Command line usage error
   * - 3
     - Configuration error
   * - 4
     - Build/compilation error
   * - 5
     - Test failure


Utility Commands
----------------

Additional utility commands:

.. list-table::
   :widths: 20 80

   * - ``info``
     - Show project information
   * - ``clean``
     - Clean build artifacts
   * - ``refresh``
     - Refresh project cache
   * - ``version``
     - Show ALY version

**Examples:**

.. code-block:: bash

   # Show project info
   aly info

   # Clean build directory
   aly clean

   # Show version
   aly version


Next Steps
----------

- :doc:`../configuration` - Configuration options
- :doc:`../api/index` - Python API
- :doc:`../examples` - Example workflows
