==========
Simulation
==========

This guide covers simulation workflows and supported tools.

.. contents::
   :local:
   :depth: 2

Overview
--------

ALY supports multiple simulation backends with a unified interface.

.. graphviz::
   :align: center
   :caption: Supported Simulators

   digraph simulators {
      rankdir=LR;
      node [shape=box, style="rounded,filled", fontname="sans-serif"];

      aly [label="aly sim", fillcolor="#e3f2fd"];

      xsim [label="Xilinx XSim", fillcolor="#fff3e0"];
      verilator [label="Verilator", fillcolor="#e8f5e9"];
      questa [label="QuestaSim", fillcolor="#f3e5f5"];

      aly -> xsim;
      aly -> verilator;
      aly -> questa;
   }


Basic Usage
-----------

Run simulation with:

.. code-block:: bash

   # Simulate with default tool
   aly sim --top tb_counter

   # Specify simulator
   aly sim --top tb_counter --tool verilator

   # Enable waveforms
   aly sim --top tb_counter --waves


Simulation Flow
---------------

.. uml::
   :align: center
   :caption: Simulation Execution Flow

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   start
   :Load testbench manifest;
   :Resolve RTL dependencies;
   :Resolve firmware dependencies;
   :Compile all sources;

   if (Compilation OK?) then (no)
      :Report errors;
      stop
   endif

   :Elaborate design;
   :Run simulation;

   if (Waveforms enabled?) then (yes)
      :Dump waveform file;
   endif

   if (GUI enabled?) then (yes)
      :Open waveform viewer;
   endif

   :Report results;
   stop
   @enduml


Tool Configuration
------------------

Configure simulators in ``.aly/config.yaml``:

XSim (Xilinx)
~~~~~~~~~~~~~

.. code-block:: yaml

   simulation:
     tools:
       xsim:
         bin: xsim
         vlog: xvlog
         xelab: xelab
         compile_opts:
           - -sv
           - -d SIMULATION
           - -i include
         elab_opts:
           - -debug typical
           - -relax
         run_opts:
           - -runall
         gui_opts:
           - -gui

Verilator
~~~~~~~~~

.. code-block:: yaml

   simulation:
     tools:
       verilator:
         bin: verilator
         args:
           - --binary
           - --trace
           - -Wall
           - -Wno-fatal
           - --timing
           - -j 4

QuestaSim
~~~~~~~~~

.. code-block:: yaml

   simulation:
     tools:
       questa:
         bin: vsim
         vlog: vlog
         vsim: vsim
         compile_opts:
           - -sv
           - +define+SIMULATION
         run_opts:
           - -c
           - -do "run -all; quit"
         gui_opts:
           - -do "add wave -r /*; run -all"


Waveform Viewing
----------------

Enable waveforms with ``--waves``:

.. code-block:: bash

   aly sim --top tb_cpu --waves

Each simulator produces different formats:

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Simulator
     - Format
     - Viewer
   * - XSim
     - .wdb
     - Vivado waveform viewer
   * - Verilator
     - .vcd / .fst
     - GTKWave
   * - QuestaSim
     - .wlf
     - QuestaSim GUI

Open waveforms in GUI:

.. code-block:: bash

   # Open with simulator GUI
   aly sim --top tb_cpu --waves --gui

   # Use GTKWave for Verilator waveforms
   aly sim --top tb_cpu --waves --gtkwave


Test Suites
-----------

Group related testbenches into suites:

.. code-block:: yaml

   # tb/manifest.yaml
   test_suites:
     - name: unit_tests
       testbenches:
         - tb_alu
         - tb_regfile
         - tb_decoder
       parallel: true

     - name: integration
       testbenches:
         - tb_cpu
         - tb_memory
       parallel: false

     - name: regression
       testbenches:
         - tb_alu
         - tb_cpu
         - tb_soc
       parallel: true
       timeout: 30m

Run suites:

.. code-block:: bash

   # Run specific suite
   aly sim --suite unit_tests

   # Run all tests (regression mode)
   aly sim --regress

   # Run specific test by name
   aly sim --test tb_alu

   # Run tests in parallel
   aly sim --suite regression -j 4

   # Stop on first failure
   aly sim --regress --stop-on-fail

   # List available tests
   aly sim --list

   # List test suites
   aly sim --list-suites

   # List tests by tag
   aly sim --list-tags


Plusargs
--------

Pass runtime arguments:

.. code-block:: bash

   aly sim --top tb_cpu \
       --plusargs FIRMWARE=boot.hex \
       --plusargs TIMEOUT=1000000 \
       --plusargs VERBOSE=1

Access in testbench:

.. code-block:: systemverilog

   string firmware_file;
   initial begin
       if ($value$plusargs("FIRMWARE=%s", firmware_file)) begin
           $display("Loading firmware: %s", firmware_file);
           $readmemh(firmware_file, memory.mem);
       end
   end


Timeouts
--------

Set simulation timeout:

.. code-block:: bash

   # Command line
   aly sim --top tb_cpu --timeout 10ms

In manifest:

.. code-block:: yaml

   testbenches:
     - name: tb_cpu
       timeout: 10ms


Show Logs
---------

Display simulation logs in real-time:

.. code-block:: bash

   aly sim --top tb_cpu --show-log


Build Directory
---------------

Simulation artifacts are stored in the build directory:

.. code-block:: text

   build/
   +-- sim/
       +-- xsim/
       |   +-- work/              # Compiled library
       |   +-- tb_cpu.wdb         # Waveforms
       +-- verilator/
       |   +-- obj_dir/           # Object files
       |   +-- Vtb_cpu            # Executable
       |   +-- trace.vcd          # Waveforms
       +-- questa/
           +-- work/              # Library
           +-- vsim.wlf           # Waveforms


Backend Comparison
------------------

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 20 20

   * - Feature
     - XSim
     - Verilator
     - QuestaSim
     - Icarus
   * - Speed
     - Medium
     - Fast
     - Medium
     - Slow
   * - SV Support
     - Full
     - Partial
     - Full
     - Limited
   * - Waveforms
     - .wdb
     - .vcd/.fst
     - .wlf
     - .vcd
   * - UVM
     - Yes
     - No
     - Yes
     - No
   * - License
     - Xilinx
     - Open Source
     - Commercial
     - Open Source


Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Compilation errors:**

Check the simulation log for details:

.. code-block:: bash

   aly sim --top tb_cpu --show-log

**Timeout:**

.. code-block:: bash

   # Increase timeout
   aly sim --top tb_cpu --timeout 1h

**Missing dependencies:**

Check manifest dependencies:

.. code-block:: yaml

   testbenches:
     - name: tb_cpu
       rtl_deps:
         - cpu_core    # Ensure this module exists
         - alu


Next Steps
----------

- :doc:`synthesis` - Synthesis workflows
- :doc:`commands/index` - Full CLI reference
- :doc:`manifest_system` - Testbench manifest details
