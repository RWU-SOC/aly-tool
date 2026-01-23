========
Examples
========

This section provides complete examples for common workflows.

.. contents::
   :local:
   :class: toc-hidden
   :depth: 2

Simple Counter Project
----------------------

A minimal project demonstrating basic ALY usage.

Project Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text

   counter_project/
   +-- .aly/
   |   +-- config.yaml
   +-- rtl/
   |   +-- manifest.yaml
   |   +-- counter.sv
   +-- tb/
   |   +-- manifest.yaml
   |   +-- tb_counter.sv
   +-- constraints/
       +-- arty_a7.xdc

Configuration
~~~~~~~~~~~~~

.. code-block:: yaml

   # .aly/config.yaml
   project:
     name: counter_demo
     version: 1.0.0
     language: systemverilog

   defaults:
     simulator: verilator
     synthesizer: vivado

RTL Manifest
~~~~~~~~~~~~

.. code-block:: yaml

   # rtl/manifest.yaml
   name: counter
   type: rtl
   language: systemverilog

   modules:
     - name: counter
       top: counter
       files:
         - counter.sv

RTL Code
~~~~~~~~

.. code-block:: systemverilog

   // rtl/counter.sv
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

Testbench
~~~~~~~~~

.. code-block:: yaml

   # tb/manifest.yaml
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

.. code-block:: systemverilog

   // tb/tb_counter.sv
   module tb_counter;
       logic       clk = 0;
       logic       rst_n;
       logic       enable;
       logic [7:0] count;

       always #5 clk = ~clk;

       counter #(.WIDTH(8)) dut (.*);

       initial begin
           $display("Starting counter test");
           rst_n = 0;
           enable = 0;
           #20 rst_n = 1;
           #10 enable = 1;
           #100;
           $display("Count = %d", count);
           assert(count == 10);
           $display("PASS");
           $finish;
       end
   endmodule

Commands
~~~~~~~~

.. code-block:: bash

   # Simulate
   aly simulate --top tb_counter

   # Lint
   aly lint

   # Synthesize
   aly synth --target arty_a7 --top counter


RISC-V SoC Project
------------------

A more complex project with CPU, peripherals, and firmware.

Project Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text

   riscv_soc/
   +-- .aly/
   |   +-- config.yaml
   +-- rtl/
   |   +-- manifest.yaml
   |   +-- cpu/
   |   |   +-- cpu_core.sv
   |   |   +-- alu.sv
   |   |   +-- decoder.sv
   |   +-- peripherals/
   |   |   +-- uart.sv
   |   |   +-- gpio.sv
   |   +-- soc_top.sv
   +-- tb/
   |   +-- manifest.yaml
   |   +-- tb_soc.sv
   +-- fw/
   |   +-- manifest.yaml
   |   +-- boot.S
   |   +-- main.c
   |   +-- linker.ld
   +-- ip/
   |   +-- axi_interconnect/
   +-- constraints/
       +-- arty_a7.xdc

Configuration
~~~~~~~~~~~~~

.. code-block:: yaml

   # .aly/config.yaml
   project:
     name: riscv_soc
     version: 1.0.0
     language: systemverilog

   features:
     firmware: true
     ip: true
     constraints: true

   defaults:
     simulator: xsim
     synthesizer: vivado

   simulation:
     default_tool: xsim
     tools:
       xsim:
         compile_opts: [-sv, -d SIMULATION]

   synthesis:
     targets:
       arty_a7:
         tool: vivado
         part: xc7a100tcsg324-1
         top: soc_top
         constraints:
           - constraints/arty_a7.xdc

RTL Manifest
~~~~~~~~~~~~

.. code-block:: yaml

   # rtl/manifest.yaml
   name: riscv_soc
   type: rtl
   language: systemverilog

   packages:
     - name: soc_pkg
       file: pkg/soc_pkg.sv
       scope: all

   modules:
     - name: alu
       top: alu
       files:
         - cpu/alu.sv

     - name: decoder
       top: decoder
       files:
         - cpu/decoder.sv
       deps:
         - alu

     - name: cpu_core
       top: cpu_core
       files:
         - cpu/cpu_core.sv
       deps:
         - alu
         - decoder

     - name: uart
       top: uart
       files:
         - peripherals/uart.sv

     - name: gpio
       top: gpio
       files:
         - peripherals/gpio.sv

     - name: soc_top
       top: soc_top
       files:
         - soc_top.sv
       deps:
         - cpu_core
         - uart
         - gpio

Firmware Manifest
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # fw/manifest.yaml
   name: soc_firmware
   type: firmware

   toolchain:
     prefix: riscv64-unknown-elf-
     march: rv32i
     mabi: ilp32
     cflags:
       - -O2
       - -Wall
       - -nostdlib
       - -ffreestanding

   builds:
     - name: bootloader
       sources:
         - boot.S
         - main.c
       linker_script: linker.ld
       outputs:
         - format: elf
         - format: hex
           base_address: 0x80000000

Testbench
~~~~~~~~~

.. code-block:: yaml

   # tb/manifest.yaml
   name: soc_tests
   type: testbench

   testbenches:
     - name: tb_soc
       top: tb_soc
       files:
         - tb_soc.sv
       rtl_deps:
         - soc_top
       fw_deps:
         - bootloader
       timeout: 10ms
       plusargs:
         FIRMWARE: "fw/bootloader.hex"

   test_suites:
     - name: regression
       testbenches:
         - tb_soc
       parallel: false

Commands
~~~~~~~~

.. code-block:: bash

   # Build firmware
   aly firmware build --name bootloader

   # Simulate with firmware
   aly simulate --top tb_soc

   # Run regression
   aly simulate --suite regression

   # Synthesize
   aly synth --target arty_a7 --impl


Multi-Target Project
--------------------

A project targeting multiple FPGA boards.

.. code-block:: yaml

   # .aly/config.yaml
   synthesis:
     targets:
       arty_a7:
         tool: vivado
         part: xc7a100tcsg324-1
         top: fpga_top
         constraints:
           - constraints/arty_a7.xdc

       nexys_a7:
         tool: vivado
         part: xc7a100tcsg324-1
         top: fpga_top
         constraints:
           - constraints/nexys_a7.xdc

       icebreaker:
         tool: yosys
         tech: ice40
         top: fpga_top
         constraints:
           - constraints/icebreaker.pcf

Commands:

.. code-block:: bash

   # Synthesize for each target
   aly synth --target arty_a7
   aly synth --target nexys_a7
   aly synth --target icebreaker


CI/CD Pipeline Example
----------------------

GitHub Actions workflow for automated testing.

.. code-block:: yaml

   # .github/workflows/ci.yml
   name: CI

   on: [push, pull_request]

   jobs:
     lint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Install tools
           run: |
             apt-get update
             apt-get install -y verilator
             pip install aly
         - name: Lint
           run: aly lint --format sarif > lint.sarif
         - uses: github/codeql-action/upload-sarif@v2
           with:
             sarif_file: lint.sarif

     simulate:
       runs-on: ubuntu-latest
       needs: lint
       steps:
         - uses: actions/checkout@v3
         - name: Install tools
           run: |
             apt-get install -y verilator
             pip install aly
         - name: Run tests
           run: aly simulate --suite regression

     synthesize:
       runs-on: ubuntu-latest
       needs: simulate
       if: github.ref == 'refs/heads/main'
       steps:
         - uses: actions/checkout@v3
         - name: Setup Vivado
           run: # Install Vivado
         - name: Synthesize
           run: aly synth --target arty_a7


IP Reuse Example
----------------

Creating and using reusable IP.

Create IP
~~~~~~~~~

.. code-block:: text

   ip/uart/
   +-- manifest.yaml
   +-- rtl/
   |   +-- uart_tx.sv
   |   +-- uart_rx.sv
   +-- tb/
       +-- tb_uart.sv

.. code-block:: yaml

   # ip/uart/manifest.yaml
   name: uart
   type: ip
   version: 1.0.0
   vendor: internal

   files:
     - rtl/uart_tx.sv
     - rtl/uart_rx.sv

   parameters:
     BAUD_RATE: 115200
     DATA_BITS: 8

Use IP
~~~~~~

.. code-block:: yaml

   # rtl/manifest.yaml
   modules:
     - name: soc_top
       files:
         - soc_top.sv
       deps:
         - uart  # Reference IP

.. code-block:: systemverilog

   // rtl/soc_top.sv
   module soc_top (
       input  clk,
       input  rst_n,
       output uart_tx,
       input  uart_rx
   );

       uart #(
           .BAUD_RATE(9600)
       ) u_uart (
           .clk(clk),
           .rst_n(rst_n),
           .tx(uart_tx),
           .rx(uart_rx)
       );

   endmodule


Waveform Debugging Example
--------------------------

Complete workflow for debugging with waveforms.

.. code-block:: bash

   # Run simulation with waves
   aly simulate --top tb_cpu --waves --tool verilator

   # View waveforms
   gtkwave build/sim/verilator/trace.vcd &

   # For XSim
   aly simulate --top tb_cpu --waves --gui --tool xsim

Add signals programmatically:

.. code-block:: systemverilog

   initial begin
       $dumpfile("trace.vcd");
       $dumpvars(0, tb_cpu);
   end


Next Steps
----------

- :doc:`commands/index` - Full command reference
- :doc:`configuration` - Configuration options
- :doc:`architecture` - Internal architecture
