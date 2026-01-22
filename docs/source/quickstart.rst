==========
Quickstart
==========

This guide walks you through creating and simulating a simple design with ALY.

Create a New Project
--------------------

Initialize a new project using the basic template:

.. code-block:: bash

   aly init counter_demo --template basic
   cd counter_demo

Project Structure
~~~~~~~~~~~~~~~~~

The template creates this structure:

.. code-block:: text

   counter_demo/
   +-- .aly/
   |   +-- config.yaml       # Project configuration
   +-- rtl/
   |   +-- manifest.yaml     # RTL module definitions
   |   +-- counter.sv        # Sample RTL
   +-- tb/
   |   +-- manifest.yaml     # Testbench definitions
   |   +-- tb_counter.sv     # Sample testbench


Create RTL Module
-----------------

Edit ``rtl/counter.sv``:

.. code-block:: systemverilog

   module counter #(
       parameter WIDTH = 8
   ) (
       input  logic             clk,
       input  logic             rst_n,
       input  logic             enable,
       output logic [WIDTH-1:0] count
   );

       always_ff @(posedge clk or negedge rst_n) begin
           if (!rst_n)
               count <= '0;
           else if (enable)
               count <= count + 1'b1;
       end

   endmodule

Update ``rtl/manifest.yaml``:

.. code-block:: yaml

   name: counter
   type: rtl
   language: systemverilog

   modules:
     - name: counter
       top: counter
       files:
         - counter.sv


Create Testbench
----------------

Edit ``tb/tb_counter.sv``:

.. code-block:: systemverilog

   module tb_counter;

       logic       clk = 0;
       logic       rst_n;
       logic       enable;
       logic [7:0] count;

       // Clock generation
       always #5 clk = ~clk;

       // DUT
       counter #(.WIDTH(8)) dut (
           .clk    (clk),
           .rst_n  (rst_n),
           .enable (enable),
           .count  (count)
       );

       // Test sequence
       initial begin
           $display("Starting counter test...");

           rst_n = 0;
           enable = 0;
           #20;

           rst_n = 1;
           #10;

           enable = 1;
           #100;

           $display("Count = %d", count);
           assert(count == 10) else $error("Count mismatch!");

           $display("Test PASSED");
           $finish;
       end

   endmodule

Update ``tb/manifest.yaml``:

.. code-block:: yaml

   name: counter_tb
   type: testbench
   language: systemverilog

   testbenches:
     - name: tb_counter
       top: tb_counter
       files:
         - tb_counter.sv
       rtl_deps:
         - counter


Run Simulation
--------------

Simulate using the default tool:

.. code-block:: bash

   # Run simulation
   aly simulate --top tb_counter

   # Run with waves enabled
   aly simulate --top tb_counter --waves

   # Use a specific simulator
   aly simulate --top tb_counter --tool verilator

Expected output:

.. code-block:: text

   [ALY] Building simulation for tb_counter...
   [ALY] Running simulation...
   Starting counter test...
   Count = 10
   Test PASSED
   [ALY] Simulation completed successfully


Lint the Design
---------------

Check for common issues:

.. code-block:: bash

   # Lint all RTL
   aly lint

   # Lint specific module
   aly lint --module counter


Synthesize
----------

Synthesize for an FPGA target:

.. code-block:: bash

   # Synthesize with Vivado
   aly synth --target arty_a7 --top counter

   # Synthesize with Yosys
   aly synth --tool yosys --top counter


Workflow Diagram
----------------

.. uml::
   :align: center
   :caption: ALY Development Workflow

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   start
   :Initialize Project;
   note right: aly init

   :Write RTL Code;
   :Create RTL Manifest;

   :Write Testbench;
   :Create TB Manifest;

   :Lint Check;
   note right: aly lint

   if (Lint OK?) then (yes)
     :Simulate;
     note right: aly simulate
   else (no)
     :Fix Issues;
     :Lint Check;
   endif

   if (Sim PASS?) then (yes)
     :Synthesize;
     note right: aly synth
   else (no)
     :Debug;
     :Simulate;
   endif

   :Program FPGA;
   note right: aly program
   stop
   @enduml


Next Steps
----------

- :doc:`concepts` - Learn about manifests, modules, and configuration
- :doc:`simulation` - Advanced simulation options
- :doc:`synthesis` - Synthesis targets and optimization
- :doc:`commands/index` - Full CLI reference
