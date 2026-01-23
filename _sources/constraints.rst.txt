=================================
Constraints (Under Development)
=================================

This guide covers design constraint management.

.. contents::
   :local:
   :class: toc-hidden
   :depth: 2

Overview
--------

Design constraints define:

- Pin assignments
- Timing requirements
- I/O standards
- Clock definitions

.. graphviz::
   :align: center
   :caption: Constraint Types

   digraph constraints {
      rankdir=LR;
      node [shape=box, style="rounded,filled", fontname="sans-serif"];

      constraints [label="Constraints", fillcolor="#e3f2fd"];

      timing [label="Timing\n(clocks, delays)", fillcolor="#e8f5e9"];
      physical [label="Physical\n(pins, placement)", fillcolor="#fff3e0"];
      io [label="I/O Standards\n(voltage, drive)", fillcolor="#f3e5f5"];

      constraints -> timing;
      constraints -> physical;
      constraints -> io;
   }


Configuration
-------------

Configure constraints in ``.aly/config.yaml``:

.. code-block:: yaml

   constraints:
     default_target: arty_a7

     sets:
       arty_a7:
         target: xc7a100tcsg324-1
         files:
           - constraints/arty_a7/pins.xdc
           - constraints/arty_a7/timing.xdc
         description: Digilent Arty A7-100T

       nexys_a7:
         target: xc7a100tcsg324-1
         files:
           - constraints/nexys_a7/master.xdc

     boards:
       arty_a7: arty_a7
       nexys_a7: nexys_a7

     clocks:
       sys_clk:
         period: 10.0
         waveform: [0.0, 5.0]
         pin: E3

     io_defaults:
       standard: LVCMOS33
       drive: 12
       slew: SLOW


XDC Constraints (Vivado)
------------------------

Xilinx Design Constraints format:

Pin Assignments
~~~~~~~~~~~~~~~

.. code-block:: tcl

   # Clock
   set_property PACKAGE_PIN E3 [get_ports clk]
   set_property IOSTANDARD LVCMOS33 [get_ports clk]

   # Reset
   set_property PACKAGE_PIN C2 [get_ports rst_n]
   set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

   # LEDs
   set_property PACKAGE_PIN H5 [get_ports {led[0]}]
   set_property PACKAGE_PIN J5 [get_ports {led[1]}]
   set_property PACKAGE_PIN T9 [get_ports {led[2]}]
   set_property PACKAGE_PIN T10 [get_ports {led[3]}]

   set_property IOSTANDARD LVCMOS33 [get_ports led[*]]

   # Buttons
   set_property PACKAGE_PIN D9 [get_ports {btn[0]}]
   set_property PACKAGE_PIN C9 [get_ports {btn[1]}]
   set_property IOSTANDARD LVCMOS33 [get_ports btn[*]]
   set_property PULLUP true [get_ports btn[*]]


Clock Constraints
~~~~~~~~~~~~~~~~~

.. code-block:: text

   # Primary clock
   create_clock -period 10.0 -name sys_clk [get_ports clk]

   # Generated clocks
   create_generated_clock -name clk_div2 \
       -source [get_ports clk] \
       -divide_by 2 \
       [get_pins clk_div_reg/Q]

   # Input clock from external device
   create_clock -period 8.0 -name ext_clk [get_ports ext_clk_in]


Timing Constraints
~~~~~~~~~~~~~~~~~~

.. code-block:: tcl

   # Input delay
   set_input_delay -clock sys_clk -max 3.0 [get_ports data_in[*]]
   set_input_delay -clock sys_clk -min 1.0 [get_ports data_in[*]]

   # Output delay
   set_output_delay -clock sys_clk -max 2.0 [get_ports data_out[*]]
   set_output_delay -clock sys_clk -min 0.5 [get_ports data_out[*]]

   # False paths
   set_false_path -from [get_ports rst_n]
   set_false_path -to [get_ports led[*]]

   # Multicycle paths
   set_multicycle_path 2 -setup -from [get_pins slow_reg/Q]
   set_multicycle_path 1 -hold -from [get_pins slow_reg/Q]


Clock Domain Crossing
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   # Async clock groups
   set_clock_groups -asynchronous \
       -group [get_clocks sys_clk] \
       -group [get_clocks ext_clk]

   # Max delay for CDC
   set_max_delay -datapath_only 5.0 \
       -from [get_clocks clk_a] \
       -to [get_clocks clk_b]


PCF Constraints (Yosys/nextpnr)
-------------------------------

Physical Constraints Format for open-source tools:

.. code-block:: text

   # Clock
   set_io clk J3

   # LEDs
   set_io led[0] C3
   set_io led[1] B3
   set_io led[2] C4
   set_io led[3] C5

   # Buttons
   set_io btn[0] A1
   set_io btn[1] A2

   # UART
   set_io uart_tx B4
   set_io uart_rx B5


SDC Constraints
---------------

Synopsys Design Constraints (ASIC flows):

.. code-block:: tcl

   # Clock definition
   create_clock -name clk -period 5.0 [get_ports clk]

   # Clock uncertainty
   set_clock_uncertainty 0.1 [get_clocks clk]

   # Transition time
   set_clock_transition 0.1 [get_clocks clk]

   # Input/output delays
   set_input_delay 1.0 -clock clk [all_inputs]
   set_output_delay 1.0 -clock clk [all_outputs]

   # Load
   set_load 0.05 [all_outputs]

   # Driving cell
   set_driving_cell -lib_cell INV_X1 [all_inputs]


CLI Commands
------------

List Constraints
~~~~~~~~~~~~~~~~

.. code-block:: bash

   aly constraints list

Output:

.. code-block:: text

   Available constraint sets:
     arty_a7    - Digilent Arty A7-100T (xc7a100tcsg324-1)
     nexys_a7   - Digilent Nexys A7 (xc7a100tcsg324-1)

Generate Template
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Generate constraint template for board
   aly constraints generate --board arty_a7 > constraints/arty_a7.xdc

Validate Constraints
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Check constraint syntax
   aly constraints validate


I/O Standards
-------------

Common FPGA I/O standards:

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Standard
     - Voltage
     - Use Case
   * - LVCMOS33
     - 3.3V
     - General purpose I/O
   * - LVCMOS18
     - 1.8V
     - Low voltage I/O
   * - LVCMOS12
     - 1.2V
     - Very low voltage
   * - LVDS_25
     - 2.5V
     - High-speed differential
   * - LVDS
     - 1.8V
     - High-speed differential
   * - SSTL15
     - 1.5V
     - DDR3 memory interface
   * - HSTL_I
     - 1.5V
     - High-speed interfaces

Example:

.. code-block:: tcl

   # 3.3V single-ended
   set_property IOSTANDARD LVCMOS33 [get_ports gpio[*]]

   # Differential LVDS
   set_property IOSTANDARD LVDS_25 [get_ports {lvds_p lvds_n}]

   # DDR memory interface
   set_property IOSTANDARD SSTL15 [get_ports ddr_*]


Board Files
-----------

Organize constraints by board:

.. code-block:: text

   constraints/
   +-- arty_a7/
   |   +-- pins.xdc         # Pin assignments
   |   +-- timing.xdc       # Timing constraints
   |   +-- debug.xdc        # Debug probes
   +-- nexys_a7/
   |   +-- master.xdc       # All constraints
   +-- custom/
       +-- timing.xdc


Template Variables
------------------

Use variables for reusable constraints:

.. code-block:: tcl

   # Variables
   set CLK_PERIOD 10.0
   set CLK_PIN E3

   # Use variables
   set_property PACKAGE_PIN $CLK_PIN [get_ports clk]
   create_clock -period $CLK_PERIOD -name sys_clk [get_ports clk]


Best Practices
--------------

1. **Separate concerns**: Keep pin, timing, and I/O constraints in separate files
2. **Comment liberally**: Document why constraints exist
3. **Use wildcards carefully**: Be specific with wildcards to avoid unintended matches
4. **Validate early**: Run constraint validation before synthesis
5. **Version control**: Track constraints with source code

Example organization:

.. code-block:: tcl

   # ==========================================
   # Arty A7 - Pin Constraints
   # ==========================================
   # Author: Your Name
   # Description: Pin assignments for Arty A7-100T
   # ==========================================

   # --------------------------------------------
   # Clock and Reset
   # --------------------------------------------
   set_property PACKAGE_PIN E3 [get_ports clk]
   set_property PACKAGE_PIN C2 [get_ports rst_n]

   # --------------------------------------------
   # User LEDs (accent, accent, accent, accent)
   # Active high
   # --------------------------------------------
   set_property PACKAGE_PIN H5  [get_ports {led[0]}]
   # ...


Next Steps
----------

- :doc:`synthesis` - Apply constraints during synthesis
- :doc:`configuration` - Full configuration reference
