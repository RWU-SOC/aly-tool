=============
IP Management
=============

This guide covers managing IP blocks in ALY projects.

.. contents::
   :local:
   :class: toc-hidden
   :depth: 2

Overview
--------

ALY supports various IP types:

.. graphviz::
   :align: center
   :caption: IP Types

   digraph ip {
      rankdir=TB;
      node [shape=box, style="rounded,filled", fontname="sans-serif"];

      ip [label="IP Blocks", fillcolor="#e3f2fd"];

      src [label="Source IP\n(RTL files)", fillcolor="#e8f5e9"];
      bin [label="Binary IP\n(precompiled)", fillcolor="#fff3e0"];
      vendor [label="Vendor IP\n(Xilinx, etc.)", fillcolor="#f3e5f5"];
      internal [label="Internal IP\n(project reuse)", fillcolor="#e0f7fa"];

      ip -> src;
      ip -> bin;
      ip -> vendor;
      ip -> internal;
   }


IP Directory Structure
----------------------

.. code-block:: text

   ip/
   +-- uart/
   |   +-- manifest.yaml
   |   +-- rtl/
   |   |   +-- uart_tx.sv
   |   |   +-- uart_rx.sv
   |   +-- tb/
   |   |   +-- tb_uart.sv
   |   +-- doc/
   |       +-- uart_spec.pdf
   +-- spi/
   |   +-- manifest.yaml
   |   +-- rtl/
   |   +-- tb/
   +-- vendor_fifo/
       +-- manifest.yaml
       +-- models/
           +-- fifo_sim.o


Creating IP
-----------

Basic IP Manifest
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # ip/uart/manifest.yaml
   name: uart
   type: ip
   version: 1.0.0
   vendor: internal
   license: Apache-2.0

   language: systemverilog

   files:
     - rtl/uart_tx.sv
     - rtl/uart_rx.sv
     - rtl/uart_fifo.sv

   includes:
     - rtl/include

   parameters:
     BAUD_RATE: 115200
     DATA_BITS: 8
     STOP_BITS: 1
     PARITY: none

   interfaces:
     - name: tx
       direction: output
       width: 1
     - name: rx
       direction: input
       width: 1
     - name: interrupt
       direction: output
       width: 1

   tags:
     - uart
     - serial
     - communication


Vendor IP
~~~~~~~~~

.. code-block:: yaml

   # ip/xilinx_fifo/manifest.yaml
   name: xilinx_fifo
   type: ip
   version: 2.1
   vendor: xilinx
   license: Proprietary

   # Precompiled simulation model
   binaries:
     simulation: models/fifo_sim.o

   compatibility:
     tools:
       - xsim
       - questa
     languages:
       - verilog
       - systemverilog

   parameters:
     DEPTH: 512
     WIDTH: 32
     ALMOST_FULL_OFFSET: 16
     ALMOST_EMPTY_OFFSET: 16


Complex IP with Nested Manifests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # ip/dma_engine/manifest.yaml
   name: dma_engine
   type: ip
   version: 1.0.0
   vendor: internal

   # Reference nested manifests
   rtl_manifest: rtl/manifest.yaml
   tb_manifest: tb/manifest.yaml
   fw_manifest: fw/manifest.yaml

   parameters:
     CHANNELS: 4
     MAX_BURST: 256


CLI Commands
------------

List IP
~~~~~~~

.. code-block:: bash

   aly ip list

Output:

.. code-block:: text

   Available IP:
     uart          v1.0.0  internal    UART controller
     spi           v1.0.0  internal    SPI master
     xilinx_fifo   v2.1    xilinx      FIFO generator

Show IP Details
~~~~~~~~~~~~~~~

.. code-block:: bash

   aly ip show uart

Output:

.. code-block:: text

   IP: uart
   Version: 1.0.0
   Vendor: internal
   License: Apache-2.0

   Files:
     - rtl/uart_tx.sv
     - rtl/uart_rx.sv
     - rtl/uart_fifo.sv

   Parameters:
     BAUD_RATE: 115200
     DATA_BITS: 8
     STOP_BITS: 1
     PARITY: none

   Interfaces:
     - tx (output, 1 bit)
     - rx (input, 1 bit)
     - interrupt (output, 1 bit)


Using IP in Projects
--------------------

Reference in RTL Manifest
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # rtl/manifest.yaml
   modules:
     - name: soc_top
       top: soc_top
       files:
         - soc_top.sv
       deps:
         - cpu_core
         - uart           # Reference IP


Reference in Testbench
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # tb/manifest.yaml
   testbenches:
     - name: tb_uart
       top: tb_uart
       files:
         - tb_uart.sv
       rtl_deps:
         - uart          # Include IP in simulation


IP Discovery
------------

ALY automatically discovers IP in the ``ip/`` directory:

.. uml::
   :align: center
   :caption: IP Discovery Flow

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   start
   :Scan ip/ directory;

   while (For each subdirectory) is (more)
      if (manifest.yaml exists?) then (yes)
         :Load manifest;
         :Validate manifest;
         :Register IP;
      endif
   endwhile (done)

   :Return IP registry;
   stop
   @enduml


IP with Internal Structure
--------------------------

For complex IP, use nested manifests:

.. code-block:: text

   ip/dma_engine/
   +-- manifest.yaml           # Main IP manifest
   +-- rtl/
   |   +-- manifest.yaml       # RTL manifest
   |   +-- dma_core.sv
   |   +-- dma_channel.sv
   |   +-- axi_master.sv
   +-- tb/
   |   +-- manifest.yaml       # Testbench manifest
   |   +-- tb_dma.sv
   +-- fw/
       +-- manifest.yaml       # Firmware manifest
       +-- dma_driver.c
       +-- dma_driver.h

Main manifest references nested:

.. code-block:: yaml

   # ip/dma_engine/manifest.yaml
   name: dma_engine
   type: ip
   version: 1.0.0

   rtl_manifest: rtl/manifest.yaml
   tb_manifest: tb/manifest.yaml
   fw_manifest: fw/manifest.yaml


Binary IP
---------

For IP with precompiled simulation models:

.. code-block:: yaml

   name: vendor_pcie
   type: ip
   vendor: vendor_name
   license: Proprietary

   # No RTL files - binary only
   binaries:
     simulation: models/pcie_bfm.o
     synthesis: netlist/pcie_core.edif

   compatibility:
     tools:
       - xsim
       - questa

Check for binary models:

.. code-block:: python

   from aly.config.models import IPManifest

   ip = IPManifest.load("ip/vendor_pcie/manifest.yaml")

   if ip.has_simulation_model():
       print("Using precompiled model")


IP Parameters
-------------

Define configurable parameters:

.. code-block:: yaml

   parameters:
     DATA_WIDTH:
       type: integer
       default: 32
       range: [8, 64]
       description: Data bus width

     DEPTH:
       type: integer
       default: 256
       values: [128, 256, 512, 1024]
       description: FIFO depth

     MODE:
       type: string
       default: "sync"
       values: ["sync", "async"]
       description: Clock mode

Override in instantiation:

.. code-block:: systemverilog

   uart #(
       .BAUD_RATE(9600),
       .DATA_BITS(8)
   ) u_uart (
       .clk(clk),
       .rst_n(rst_n),
       // ...
   );


IP Interfaces
-------------

Document interfaces:

.. code-block:: yaml

   interfaces:
     - name: s_axi
       type: axi4_lite
       direction: slave
       description: Configuration interface

     - name: m_axi
       type: axi4
       direction: master
       description: Data interface

     - name: irq
       direction: output
       width: 4
       description: Interrupt outputs


Best Practices
--------------

1. **Version your IP**: Use semantic versioning
2. **Document parameters**: Include descriptions and valid ranges
3. **Include testbenches**: Provide self-test capability
4. **Specify compatibility**: List supported tools and languages
5. **License clearly**: Specify license for each IP

.. code-block:: yaml

   # Well-documented IP manifest
   name: axi_interconnect
   type: ip
   version: 2.1.0
   vendor: internal
   license: Apache-2.0
   description: |
     AXI4 crossbar interconnect with configurable
     master/slave ports and address mapping.

   maintainers:
     - name: John Doe
       email: john@example.com

   tags:
     - axi
     - interconnect
     - noc

   discoverable: true


Next Steps
----------

- :doc:`manifest_system` - Full manifest reference
- :doc:`simulation` - Simulating with IP
- :doc:`synthesis` - Synthesizing with IP
