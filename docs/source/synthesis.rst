=========
Synthesis
=========

This guide covers synthesis workflows for FPGA and ASIC targets.

.. contents::
   :local:
   :depth: 2

Overview
--------

ALY supports multiple synthesis backends:

.. graphviz::
   :align: center
   :caption: Synthesis Backends

   digraph synth {
      rankdir=LR;
      node [shape=box, style="rounded,filled", fontname="sans-serif"];

      aly [label="aly synth", fillcolor="#e3f2fd"];

      vivado [label="Vivado\n(Xilinx FPGA)", fillcolor="#fff3e0"];
      yosys [label="Yosys\n(Open Source)", fillcolor="#e8f5e9"];

      ice40 [label="iCE40", fillcolor="#eceff1"];
      ecp5 [label="ECP5", fillcolor="#eceff1"];
      gowin [label="Gowin", fillcolor="#eceff1"];
      asic [label="ASIC", fillcolor="#eceff1"];

      aly -> vivado;
      aly -> yosys;

      yosys -> ice40;
      yosys -> ecp5;
      yosys -> gowin;
      yosys -> asic;
   }


Basic Usage
-----------

.. code-block:: bash

   # Synthesize for configured target
   aly synth --target arty_a7

   # Specify tool explicitly
   aly synth --tool vivado --top fpga_top

   # Use Yosys for iCE40
   aly synth --tool yosys --tech ice40 --top my_design


Synthesis Flow
--------------

.. uml::
   :align: center
   :caption: Synthesis Flow

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   start
   :Load RTL manifest;
   :Load synthesis config;
   :Resolve module dependencies;
   :Collect source files;

   :Generate synthesis script;
   note right: TCL for Vivado\nYS for Yosys

   :Run synthesis;

   if (Synthesis OK?) then (no)
      :Report errors;
      stop
   endif

   if (Implementation?) then (yes)
      :Place & Route;

      if (Timing met?) then (no)
         :Report violations;
      endif

      :Generate bitstream;
   endif

   :Generate reports;
   stop
   @enduml


Target Configuration
--------------------

Configure synthesis targets in ``.aly/config.yaml``:

.. code-block:: yaml

   synthesis:
     default_tool: vivado
     build_dir: build/synth

     targets:
       arty_a7:
         tool: vivado
         part: xc7a100tcsg324-1
         top: fpga_top
         constraints:
           - constraints/arty_a7/pins.xdc
           - constraints/arty_a7/timing.xdc
         options:
           strategy: Flow_PerfOptimized_high

       nexys_a7:
         tool: vivado
         part: xc7a100tcsg324-1
         top: fpga_top
         constraints:
           - constraints/nexys_a7.xdc

       ice40_hx8k:
         tool: yosys
         tech: ice40
         top: my_design
         constraints:
           - constraints/ice40.pcf

       asic_sky130:
         tool: yosys
         tech: generic
         library: sky130_hd
         top: chip_top


Vivado Synthesis
----------------

Tool Configuration
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   synthesis:
     tools:
       vivado:
         bin: vivado
         threads: 8
         batch_opts:
           - -mode
           - batch
           - -notrace

Vivado Options
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Option
     - Description
   * - ``strategy``
     - Synthesis strategy (Default, Flow_PerfOptimized_high, etc.)
   * - ``flatten_hierarchy``
     - Hierarchy handling (none, rebuilt, full)
   * - ``retiming``
     - Enable register retiming
   * - ``fsm_extraction``
     - FSM encoding (auto, one_hot, sequential)

Example:

.. code-block:: yaml

   targets:
     high_perf:
       tool: vivado
       part: xcvu9p-flga2104-2L-e
       top: top_module
       options:
         strategy: Flow_PerfOptimized_high
         flatten_hierarchy: rebuilt
         retiming: true


Yosys Synthesis
---------------

Yosys supports multiple technology targets.

Tool Configuration
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   synthesis:
     tools:
       yosys:
         bin: yosys
         script_ext: .ys

Technology Targets
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Tech
     - Description
     - Backend
   * - ``generic``
     - Generic cells
     - No P&R
   * - ``ice40``
     - Lattice iCE40
     - nextpnr-ice40
   * - ``ecp5``
     - Lattice ECP5
     - nextpnr-ecp5
   * - ``gowin``
     - Gowin FPGAs
     - nextpnr-gowin

Example:

.. code-block:: yaml

   targets:
     icebreaker:
       tool: yosys
       tech: ice40
       device: up5k
       package: sg48
       top: top_module
       constraints:
         - constraints/icebreaker.pcf


ASIC Synthesis
--------------

For ASIC flows, configure cell libraries:

.. code-block:: yaml

   synthesis:
     libraries:
       sky130_hd:
         liberty: libs/sky130_fd_sc_hd__tt_025C_1v80.lib
         verilog: libs/sky130_fd_sc_hd.v
         lef: libs/sky130_fd_sc_hd.lef
         description: Sky130 high density cells

     targets:
       asic_top:
         tool: yosys
         tech: generic
         library: sky130_hd
         top: chip_top
         options:
           abc_script: scripts/abc_opt.script


Constraints
-----------

Apply design constraints:

.. code-block:: bash

   # Use configured constraints
   aly synth --target arty_a7

   # Override constraints
   aly synth --target arty_a7 \
       --constraints constraints/custom.xdc

XDC (Vivado)
~~~~~~~~~~~~

.. code-block:: tcl

   # Clock definition
   create_clock -period 10.0 -name sys_clk [get_ports clk]

   # Pin assignments
   set_property PACKAGE_PIN E3 [get_ports clk]
   set_property IOSTANDARD LVCMOS33 [get_ports clk]

   # Timing constraints
   set_input_delay -clock sys_clk 2.0 [get_ports data_in]
   set_output_delay -clock sys_clk 1.0 [get_ports data_out]

PCF (Yosys/nextpnr)
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   set_io clk J3
   set_io led[0] C3
   set_io led[1] B3
   set_io btn A1


Implementation
--------------

Run full implementation (place & route):

.. code-block:: bash

   aly synth --target arty_a7 --impl

Implementation generates:

- Placement results
- Routing results
- Timing analysis
- Bitstream file


Reports
-------

Generate synthesis reports:

.. code-block:: bash

   aly synth --target arty_a7 --report

Available reports:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Report
     - Description
   * - ``utilization``
     - Resource usage (LUTs, FFs, BRAMs)
   * - ``timing``
     - Timing summary and violations
   * - ``power``
     - Power estimation
   * - ``drc``
     - Design rule checks

Reports are saved to:

.. code-block:: text

   build/synth/vivado/reports/
   +-- utilization.rpt
   +-- timing_summary.rpt
   +-- power.rpt


Incremental Synthesis
---------------------

For faster iteration:

.. code-block:: bash

   # First run - full synthesis
   aly synth --target arty_a7

   # Subsequent runs - incremental
   aly synth --target arty_a7 --incremental


Build Artifacts
---------------

Synthesis outputs:

.. code-block:: text

   build/synth/
   +-- vivado/
   |   +-- project.xpr         # Vivado project
   |   +-- project.runs/       # Run directories
   |   +-- fpga_top.bit        # Bitstream
   |   +-- fpga_top.ltx        # Debug probes
   |   +-- reports/            # Reports
   +-- yosys/
       +-- synth.ys            # Synthesis script
       +-- synth.json          # Netlist
       +-- pnr.log             # P&R log
       +-- design.bin          # Bitstream


Multi-Clock Designs
-------------------

Handle multiple clock domains:

.. code-block:: yaml

   constraints:
     clocks:
       sys_clk:
         period: 10.0
         waveform: [0.0, 5.0]
         pin: E3

       pcie_clk:
         period: 4.0
         waveform: [0.0, 2.0]
         pin: F10

       ddr_clk:
         period: 2.5
         waveform: [0.0, 1.25]


Debug Cores
-----------

Add debug cores (Vivado):

.. code-block:: yaml

   targets:
     arty_debug:
       tool: vivado
       part: xc7a100tcsg324-1
       top: fpga_top
       options:
         debug_cores:
           - type: ila
             depth: 4096
             probes:
               - signal: cpu/pc
                 width: 32
               - signal: cpu/instruction
                 width: 32


Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Timing violations:**

.. code-block:: bash

   # Check timing report
   cat build/synth/vivado/reports/timing_summary.rpt

   # Try different strategy
   aly synth --target arty_a7 --option strategy=Flow_PerfOptimized_high

**High utilization:**

- Check report for specific resources
- Consider design optimizations
- Use larger FPGA part

**Synthesis errors:**

.. code-block:: bash

   # Verbose output
   aly synth --target arty_a7 -v

   # Check logs
   cat build/synth/vivado/synth.log


Next Steps
----------

- :doc:`constraints` - Constraint management
- :doc:`linting` - Pre-synthesis checks
- :doc:`commands/index` - Full CLI reference
