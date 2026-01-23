=============
Core Concepts
=============

Understanding ALY's core concepts will help you effectively manage your HDL projects.

.. contents::
   :local:
   :class: toc-hidden
   :depth: 2

Project Structure
-----------------

An ALY project follows a hierarchical structure with clear separation of concerns:

.. graphviz::
   :align: center
   :caption: ALY Project Structure

   digraph project {
      rankdir=TB;
      node [shape=folder, style=filled, fontname="sans-serif"];
      edge [fontname="sans-serif"];

      root [label="Project Root", fillcolor="#e3f2fd"];
      aly [label=".aly/", fillcolor="#fff3e0"];
      rtl [label="rtl/", fillcolor="#e8f5e9"];
      tb [label="tb/", fillcolor="#fce4ec"];
      fw [label="fw/", fillcolor="#f3e5f5"];
      ip [label="ip/", fillcolor="#e0f7fa"];
      constraints [label="constraints/", fillcolor="#fff8e1"];
      build [label="build/", fillcolor="#eceff1"];

      root -> aly;
      root -> rtl;
      root -> tb;
      root -> fw;
      root -> ip;
      root -> constraints;
      root -> build;

      config [shape=note, label="config.yaml", fillcolor="#ffffff"];
      aly -> config;
   }


Manifest System
---------------

ALY uses YAML manifests to describe project components. Each component type has its own manifest format.

.. uml::
   :align: center
   :caption: Manifest Hierarchy

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   package "Project" {
      [config.yaml] as config
   }

   package "RTL" {
      [rtl/manifest.yaml] as rtl
      [RTLModule] as rtlmod
   }

   package "Testbench" {
      [tb/manifest.yaml] as tb
      [Testbench] as tbmod
      [TestSuite] as suite
   }

   package "Firmware" {
      [fw/manifest.yaml] as fw
      [FirmwareBuild] as fwbuild
   }

   package "IP" {
      [ip/*/manifest.yaml] as ip
      [IPManifest] as ipmod
   }

   config --> rtl : references
   config --> tb : references
   config --> fw : references

   rtl --> rtlmod : defines
   tb --> tbmod : defines
   tb --> suite : groups
   fw --> fwbuild : defines
   ip --> ipmod : defines

   tbmod --> rtlmod : depends on
   tbmod --> fwbuild : may include
   @enduml


Manifest Types
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 35 50

   * - Type
     - Purpose
     - Key Fields
   * - ``rtl``
     - RTL source code
     - ``modules``, ``packages``, ``includes``
   * - ``testbench``
     - Simulation testbenches
     - ``testbenches``, ``test_suites``, ``rtl_deps``
   * - ``firmware``
     - Embedded firmware
     - ``builds``, ``toolchain``, ``outputs``
   * - ``ip``
     - Vendor IP blocks
     - ``files``, ``binaries``, ``interfaces``


RTL Modules
-----------

RTL modules represent synthesizable hardware blocks. They can be organized hierarchically.

Module Definition
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # rtl/manifest.yaml
   name: my_design
   type: rtl
   language: systemverilog

   modules:
     - name: alu
       top: alu
       files:
         - alu.sv
         - adder.sv
         - shifter.sv

     - name: cpu_core
       top: cpu_core
       files:
         - cpu_core.sv
       deps:
         - alu    # Depends on ALU module

Module Hierarchy
~~~~~~~~~~~~~~~~

.. graphviz::
   :align: center
   :caption: Module Dependency Graph

   digraph modules {
      rankdir=BT;
      node [shape=component, style=filled, fillcolor="#e8f5e9", fontname="sans-serif"];
      edge [fontname="sans-serif"];

      cpu [label="cpu_core"];
      alu [label="alu"];
      adder [label="adder"];
      shifter [label="shifter"];
      regfile [label="register_file"];

      cpu -> alu;
      cpu -> regfile;
      alu -> adder;
      alu -> shifter;
   }


File Resolution
~~~~~~~~~~~~~~~

ALY supports multiple ways to specify source files:

.. code-block:: yaml

   modules:
     - name: design
       files:
         # Direct file paths
         - core.sv
         - utils/helpers.sv

         # Glob patterns
         - "*.sv"
         - "subdir/**/*.v"

       # Exclusions
       excludes:
         - "*_tb.sv"
         - "deprecated/**"


Testbenches
-----------

Testbenches define simulation environments and test cases.

.. code-block:: yaml

   # tb/manifest.yaml
   name: my_tests
   type: testbench
   language: systemverilog

   testbenches:
     - name: tb_alu
       top: tb_alu
       files:
         - tb_alu.sv
       rtl_deps:
         - alu
       timeout: 1000us

   test_suites:
     - name: regression
       testbenches:
         - tb_alu
         - tb_cpu
       parallel: true


Dependency Types
~~~~~~~~~~~~~~~~

.. uml::
   :align: center
   :caption: Testbench Dependencies

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   rectangle "Testbench" as TB {
      component "tb_cpu.sv" as tb
   }

   rectangle "RTL Dependencies" as RTL {
      component "cpu_core" as cpu
      component "alu" as alu
   }

   rectangle "Firmware" as FW {
      component "boot.hex" as boot
   }

   rectangle "Packages" as PKG {
      component "uvm_pkg" as uvm
   }

   tb --> cpu : rtl_deps
   tb --> boot : fw_deps
   tb --> uvm : pkg_deps
   cpu --> alu : internal
   @enduml


Firmware Builds
---------------

Firmware manifests define embedded software builds for processor cores.

.. code-block:: yaml

   # fw/manifest.yaml
   name: firmware
   type: firmware

   toolchain:
     prefix: riscv64-unknown-elf-
     march: rv32i
     mabi: ilp32
     cflags:
       - -O2
       - -Wall

   builds:
     - name: bootloader
       sources:
         - boot.c
         - startup.S
       linker_script: linker.ld
       outputs:
         - format: elf
         - format: hex
           base_address: 0x80000000


Build Pipeline
~~~~~~~~~~~~~~

.. uml::
   :align: center
   :caption: Firmware Build Flow

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   start
   :Source Files (.c, .S);
   :Compile (GCC);
   :Object Files (.o);
   :Link (linker.ld);
   :ELF Binary;

   fork
     :objcopy;
     :Binary (.bin);
   fork again
     :objcopy;
     :Intel HEX (.hex);
   fork again
     :Custom Script;
     :Verilog MEM (.mem);
   end fork

   stop
   @enduml


IP Management
-------------

IP blocks represent reusable or vendor-provided components.

.. code-block:: yaml

   # ip/uart/manifest.yaml
   name: uart_ip
   type: ip
   vendor: xilinx
   version: 1.0.0

   # Option 1: Direct files
   files:
     - rtl/uart_tx.sv
     - rtl/uart_rx.sv

   # Option 2: Precompiled models
   binaries:
     simulation: models/uart_sim.o

   parameters:
     BAUD_RATE: 115200
     DATA_WIDTH: 8


IP Types
~~~~~~~~

.. graphviz::
   :align: center
   :caption: IP Classification

   digraph ip_types {
      rankdir=LR;
      node [shape=box, style="rounded,filled", fontname="sans-serif"];

      ip [label="IP Block", fillcolor="#e3f2fd"];

      src [label="Source IP\n(RTL files)", fillcolor="#e8f5e9"];
      bin [label="Binary IP\n(simulation models)", fillcolor="#fff3e0"];
      hybrid [label="Hybrid IP\n(both)", fillcolor="#f3e5f5"];

      ip -> src;
      ip -> bin;
      ip -> hybrid;
   }


Configuration Hierarchy
-----------------------

ALY uses a hierarchical configuration system that allows global defaults with per-component overrides.

.. uml::
   :align: center
   :caption: Configuration Resolution

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   rectangle "Project Config\n(.aly/config.yaml)" as proj #e3f2fd
   rectangle "Component Manifest\n(rtl/manifest.yaml)" as comp #e8f5e9
   rectangle "Module Override\n(module entry)" as mod #fff3e0
   rectangle "CLI Override\n(--option)" as cli #fce4ec
   rectangle "Effective Config" as eff #c8e6c9

   proj --> comp : inherits
   comp --> mod : overrides
   mod --> cli : overrides
   cli --> eff : produces
   @enduml


Build System
------------

ALY manages build artifacts in a structured output directory.

.. code-block:: text

   build/
   +-- sim/                    # Simulation outputs
   |   +-- xsim/              # XSim-specific files
   |   +-- verilator/         # Verilator-specific files
   +-- synth/                  # Synthesis outputs
   |   +-- vivado/            # Vivado project files
   |   +-- yosys/             # Yosys outputs
   +-- fw/                     # Firmware outputs
       +-- bootloader/        # Per-build outputs


Backend Architecture
~~~~~~~~~~~~~~~~~~~~

.. uml::
   :align: center
   :caption: Tool Backend System

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   interface "SimulatorBackend" as sim
   interface "SynthBackend" as synth

   class XSimBackend
   class QuestaBackend
   class VerilatorBackend

   class VivadoBackend
   class YosysBackend

   sim <|.. XSimBackend
   sim <|.. QuestaBackend
   sim <|.. VerilatorBackend

   synth <|.. VivadoBackend
   synth <|.. YosysBackend
   @enduml


Next Steps
----------

- :doc:`configuration` - Detailed configuration options
- :doc:`manifest_system` - Complete manifest reference
- :doc:`architecture` - Internal architecture details
