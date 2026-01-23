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
     - name: register_file
       top: register_file
       files:
         - register_file.sv
     - name: cpu_core
       top: cpu_core
       files:
         - cpu_core.sv
       dependencies:
        - name: rv64i_pkg
          type: package
        - name: alu
          type: rtl
        - name: register_file
          type: rtl

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
      description: ALU unit test
      top: tb_alu
      files:
        - tb_alu.sv
      dependencies:
        - name: alu
          type: rtl
        - name: rv64i_pkg
          type: package
      default_timeout: 10000
      tags: [unit, alu]
      - name: tb_cpu
        description: CPU core integration test
        top: tb_cpu
        files:
          - tb_cpu.sv
        dependencies:
          - name: cpu_core
            type: rtl
          - name: boot
            type: firmware
          - name: core_pkg
            type: package
        default_timeout: 50000
        tags: [integration, cpu]

   test_suites:
     - name: regression
       testbenches:
         - tb_alu
         - tb_cpu
       parallel: 4 # Number of parallel jobs


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
      component "core_pkg" as uvm
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
    name: instr_test
    type: firmware
    author: Mohamed Aly
    version: 1.0.0

    toolchain: riscv64

    builds:
      # ASM builds
      - name: allinstructions
        languages: [asm]
        sources: [allinstructions.asm]
        includes: [include/]
        linker_script: linkers/memory.ld
        flags:
          common: [-fno-builtin, -nostdlib]
          asm: [-x]
          ld: [-nostartfiles]
        outputs:
          - format: elf
            
          - format: mem
            
            plusarg: MEM_FILE
        mem:
          - name: memory_le.mem
            format: mem
            word_width: 64
            byte_order: little
      - name: instr01loadbyte
    languages: [asm]
    sources: [instr01loadbyte.asm]
    includes: [include/]
    linker_script: linkers/memory.ld
    flags:
      common: [-fno-builtin, -nostdlib]
      asm: [-x]
      ld: [-nostartfiles]
    outputs:
      - format: elf
        
      - format: mem
        
        plusarg: MEM_FILE
    mem:
      - name: memory_le.mem
        format: mem
        word_width: 64
        byte_order: little
        

  - name: instr02loadhalf
    languages: [asm]
    sources: [instr02loadhalf.asm]
    includes: [include/]
    linker_script: linkers/memory.ld
    flags:
      common: [-fno-builtin, -nostdlib]
      asm: [-x]
      ld: [-nostartfiles]
    outputs:
      - format: elf
        
      - format: mem
        
        plusarg: MEM_FILE
    mem:
      - name: memory_le.mem
        format: mem
        word_width: 64
        byte_order: little


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
   description: Parameterized UART IP Core
   version: 1.0.0

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
      tb [label="IP Testbenches\n(simulation)", fillcolor="#fff3e0"];
      fw [label="Firmware for intructions testing\n(optional)", fillcolor="#f3e5f5"];

      ip -> src;
      ip -> tb;
      ip -> fw;
   }


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
