===============
Manifest System
===============

ALY uses YAML manifests to describe project components. This reference covers all manifest types and their fields.

.. contents::
   :local:
   :depth: 2

Overview
--------

Each component type has its own manifest format. Manifests are typically named ``manifest.yaml`` and placed in their respective directories.

.. graphviz::
   :align: center
   :caption: Manifest Types

   digraph manifests {
      rankdir=TB;
      node [shape=note, style=filled, fontname="sans-serif"];

      rtl [label="RTL Manifest\nrtl/manifest.yaml", fillcolor="#e8f5e9"];
      tb [label="Testbench Manifest\ntb/manifest.yaml", fillcolor="#fce4ec"];
      fw [label="Firmware Manifest\nfw/manifest.yaml", fillcolor="#f3e5f5"];
      ip [label="IP Manifest\nip/*/manifest.yaml", fillcolor="#e0f7fa"];
   }


RTL Manifest
------------

RTL manifests define synthesizable hardware modules.

Schema
~~~~~~

.. code-block:: yaml

   # rtl/manifest.yaml
   name: <string>           # Required: manifest name
   type: rtl                # Required: must be "rtl"
   version: <string>        # Optional: version (default: "1.0.0")
   description: <string>    # Optional: manifest description
   author: <string>         # Optional: author name
   license: <string>        # Optional: license identifier
   vendor: <string>         # Optional: vendor name
   language: <string>       # Optional: verilog|systemverilog|vhdl

   # Top module reference (name of a module in modules list)
   top: <string>

   # Global settings applied to all modules
   includes: [<paths>]      # Include directories
   defines:                 # Preprocessor defines
     KEY: value

   # Package definitions (for SystemVerilog packages)
   packages:
     - path: <path>         # Required: package file path
       name: <string>       # Optional: package name
       modules: [<list>]    # Optional: which modules use this package (empty = all)

   # Module definitions
   modules:
     - name: <string>       # Required: module identifier
       author: <string>     # Optional: module author
       version: <string>    # Optional: module version
       language: <string>   # Optional: module language
       top: <string>        # Optional: top-level module name
       files: [<paths>]     # Source files (supports globs)
       dependencies:        # Module dependencies
         - name: <string>   # Dependency name
           type: <string>   # rtl|package


Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   name: rv64i_core
   type: rtl
   version: 1.0.0
   language: systemverilog

   modules:
     - name: rv64i_core
       language: systemverilog
       files:
         - CPU.sv
         - PC.sv
       dependencies:
         - name: rv64i_pkg
           type: package

         - name: alu
           type: rtl

         - name: decoder
           type: rtl

         - name: regfile
           type: rtl

     - name: alu
       language: systemverilog
       top: alu
       files:
         - alu/*.sv

     - name: regfile
       files:
         - regfile/register_file.sv
         - regfile/reg_read.sv
         - regfile/reg_write.sv

     - name: decoder
       files:
         - decoder.sv
       dependencies:
         - name: alu
           type: rtl


Module Class Diagram
~~~~~~~~~~~~~~~~~~~~

.. uml::
   :align: center
   :caption: RTLManifest Structure

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   class RTLManifest {
      +name: str
      +type: str
      +version: str
      +language: str
      +modules: List[RTLModule]
      +packages: List[RTLPackage]
      +includes: List[str]
      +defines: Dict[str, str]
      --
      +get_module(name): RTLModule
      +get_all_files(): List[Path]
      +validate(): List[ValidationMessage]
   }

   class RTLModule {
      +name: str
      +author: str
      +top: str
      +version: str
      +language: str
      +files: List[str]
      +dependencies: List[Dict]
      --
      +resolve_files(): List[Path]
   }

   class RTLPackage {
      +path: str
      +name: str
      +modules: List[str]
      --
      +to_dict(): Dict
   }

   RTLManifest "1" *-- "*" RTLModule
   RTLManifest "1" *-- "*" RTLPackage
   @enduml


Testbench Manifest
------------------

Testbench manifests define simulation environments.

Schema
~~~~~~

.. code-block:: yaml

   # tb/manifest.yaml
   name: <string>           # Required: manifest name
   type: testbench          # Required: must be "testbench"
   version: <string>        # Optional: version
   description: <string>    # Optional: description
   author: <string>         # Optional: author

   # Testbench definitions
   testbenches:
     - name: <string>       # Required: testbench identifier
       description: <string> # Optional: testbench description
       top: <string>        # Optional: top module name (defaults to name)
       files: [<paths>]     # Testbench source files
       includes: [<paths>]  # Include directories
       defines: {}          # Preprocessor defines
       dependencies:        # Dependencies
         - name: <string>   # Dependency name
           type: <string>   # rtl|firmware|package
       default_timeout: <int|str>  # Simulation timeout (int or "forever")
       plusargs: {}         # Runtime plusargs
       tags: [<tags>]       # Tags for filtering

   # Test suites (group testbenches)
   testsuites:
     - name: <string>       # Suite name
       description: <string> # Suite description
       testbenches: [<names>]  # List of testbench names
       parallel: <int>      # Number of parallel jobs
       timeout: <int>       # Suite-level timeout (seconds)
       stop_on_fail: <bool> # Stop on first failure


Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   name: rv64imac_tb
   type: testbench
   version: 1.0.0
   description: Testbenches for RV64IMAC processor
   author: Mohamed Aly

   testbenches:
     - name: tb_rv64i
       description: Base RV64I testbench
       top: tb_rv64i
       files:
         - tb_rv64i.sv
       dependencies:
         - name: rv64i_soc
           type: rtl
         - name: rv64i_pkg
           type: package
         - name: rv64i
           type: firmware
       default_timeout: 100000
       tags: [integration]

     - name: tb_rv64i_alu
       description: ALU instruction test
       top: tb_rv64i
       files:
         - tb_rv64i_alu.sv
       dependencies:
         - name: rv64i_soc
           type: rtl
         - name: alu_test
           type: firmware
       default_timeout: 100000
       tags: [unit, alu]

   testsuites:
     - name: instruction_tests
       description: All instruction tests
       testbenches:
         - tb_rv64i
         - tb_rv64i_alu
       parallel: 4
       timeout: 60

     - name: regression
       description: Full regression suite
       testbenches:
         - tb_rv64i
         - tb_rv64i_alu
       parallel: 1
       stop_on_fail: true


Testbench Class Diagram
~~~~~~~~~~~~~~~~~~~~~~~

.. uml::
   :align: center
   :caption: TestbenchManifest Structure

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   class TestbenchManifest {
      +name: str
      +type: str
      +testbenches: List[Testbench]
      +test_suites: List[TestSuite]
      +packages: List[RTLPackage]
      --
      +get_testbench(name): Testbench
      +get_suite(name): TestSuite
   }

   class Testbench {
      +name: str
      +description: str
      +top: str
      +files: List[str]
      +includes: List[str]
      +defines: Dict[str, str]
      +dependencies: List[Dict]
      +default_timeout: int|str
      +plusargs: Dict[str, str]
      +tags: List[str]
      --
      +resolve_files(): List[Path]
      +get_rtl_deps(): List[Dict]
      +get_firmware_deps(): List[Dict]
      +get_package_deps(): List[Dict]
   }

   class TestSuite {
      +name: str
      +description: str
      +testbenches: List[str]
      +parallel: int
      +timeout: int
      +stop_on_fail: bool
   }

   TestbenchManifest "1" *-- "*" Testbench
   TestbenchManifest "1" *-- "*" TestSuite
   TestSuite --> Testbench : references
   @enduml


Firmware Manifest
-----------------

Firmware manifests define embedded software builds.

Schema
~~~~~~

.. code-block:: yaml

   # fw/manifest.yaml
   name: <string>           # Required: manifest name
   type: firmware           # Required: must be "firmware"
   version: <string>        # Optional: version
   description: <string>    # Optional: description
   author: <string>         # Optional: author

   # Default toolchain (can be overridden per-build)
   toolchain: <string>      # Reference to toolchain name in toolchains.yaml

   # Build definitions
   builds:
     - name: <string>       # Required: build identifier
       author: <string>     # Optional: build author
       version: <string>    # Optional: build version
       languages: [<langs>] # Languages used (c, asm)
       sources: [<paths>]   # Source files (.c, .S, .asm)
       includes: [<paths>]  # Include directories
       linker_script: <path>  # Linker script
       toolchain: <string>  # Override toolchain
       defines: {}          # Preprocessor defines
       flags:               # Compiler/linker flags
         common: [<flags>]  # Flags for all tools
         c: [<flags>]       # C compiler flags
         asm: [<flags>]     # Assembler flags
         ld: [<flags>]      # Linker flags
       outputs:             # Output formats
         - format: elf|bin|hex|mem|coe|lst|map|disasm
           required: <bool>
           plusarg: <string>  # Plusarg name for simulation
       mem:                 # Memory file configuration
         - name: <string>   # Output filename
           format: <string> # Format (mem, hex, coe)
           word_width: <int>  # Word width (8, 16, 32, 64)
           byte_order: <string>  # little|big


Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   name: instr_test
   type: firmware
   author: Mohamed Aly
   version: 1.0.0

   toolchain: riscv64

   builds:
     - name: bootloader
       languages: [asm, c]
       sources:
         - boot/start.S
         - boot/main.c
       includes:
         - include/
       linker_script: linkers/memory.ld
       flags:
         common: [-fno-builtin, -nostdlib]
         c: [-O2, -Wall]
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

     - name: application
       languages: [c]
       sources:
         - app/*.c
       includes:
         - include/
       linker_script: linkers/memory.ld
       flags:
         common: [-fno-builtin, -nostdlib]
         c: [-O2, -Wall]
         ld: [-nostartfiles]
       outputs:
         - format: elf
         - format: mem
       mem:
         - name: memory.mem
           format: mem
           word_width: 64
           byte_order: little


Firmware Class Diagram
~~~~~~~~~~~~~~~~~~~~~~

.. uml::
   :align: center
   :caption: FirmwareManifest Structure

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   class FirmwareManifest {
      +name: str
      +type: str
      +toolchain: str
      +builds: List[FirmwareBuild]
      --
      +get_build(name): FirmwareBuild
      +get_build_names(): List[str]
   }

   class FirmwareBuild {
      +name: str
      +author: str
      +version: str
      +languages: List[str]
      +sources: List[str]
      +includes: List[str]
      +linker_script: str
      +toolchain: str
      +defines: Dict[str, str]
      +flags: FirmwareFlags
      +outputs: List[OutputSpec]
      +mem: List[MemFormat]
      --
      +resolve_files(): List[Path]
      +get_source_files(): List[Path]
   }

   class FirmwareFlags {
      +common: List[str]
      +c: List[str]
      +asm: List[str]
      +ld: List[str]
   }

   class OutputSpec {
      +format: str
      +required: bool
      +plusarg: str
   }

   class MemFormat {
      +name: str
      +format: str
      +word_width: int
      +byte_order: str
   }

   FirmwareManifest "1" *-- "*" FirmwareBuild
   FirmwareBuild "1" *-- "1" FirmwareFlags
   FirmwareBuild "1" *-- "*" OutputSpec
   FirmwareBuild "1" *-- "*" MemFormat
   @enduml


IP Manifest
-----------

IP manifests define reusable or vendor-provided IP blocks.

Schema
~~~~~~

.. code-block:: yaml

   # ip/<name>/manifest.yaml
   name: <string>           # Required: IP name
   type: ip                 # Required: must be "ip"
   version: <string>        # Version
   vendor: <string>         # Vendor name
   license: <string>        # License type

   language: <string>       # HDL language

   # Source files (for source IP)
   files: [<paths>]
   includes: [<paths>]
   defines: {}

   # Precompiled models (for binary IP)
   binaries:
     simulation: <path>     # Precompiled simulation model

   # Tool compatibility
   compatibility:
     tools: [<tools>]       # Compatible simulators
     languages: [<langs>]   # Supported languages

   # Design metadata
   parameters:              # Configurable parameters
     PARAM_NAME: value
   interfaces:              # Port interfaces
     - name: <string>
       direction: input|output|inout
       width: <int>

   # Discovery metadata
   discoverable: <bool>
   tags: [<tags>]
   namespace: <string>

   # Nested manifests (for complex IP)
   rtl_manifest: <path>     # Internal RTL manifest
   tb_manifest: <path>      # Internal testbench manifest
   fw_manifest: <path>      # Internal firmware manifest


Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   name: axi_uart
   type: ip
   version: 2.1.0
   vendor: xilinx
   license: Proprietary

   language: systemverilog

   files:
     - rtl/axi_uart.sv
     - rtl/uart_tx.sv
     - rtl/uart_rx.sv
     - rtl/axi_slave.sv

   includes:
     - include

   compatibility:
     tools:
       - xsim
       - questa
       - verilator
     languages:
       - systemverilog
       - verilog

   parameters:
     BAUD_RATE: 115200
     DATA_BITS: 8
     STOP_BITS: 1
     PARITY: none
     FIFO_DEPTH: 16

   interfaces:
     - name: s_axi
       direction: inout
       type: axi4_lite

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
     - axi
     - communication
   namespace: xilinx


IP with Nested Manifests
~~~~~~~~~~~~~~~~~~~~~~~~

Complex IP can have internal structure:

.. code-block:: yaml

   name: complex_ip
   type: ip
   version: 1.0.0
   vendor: internal

   # Reference nested manifests
   rtl_manifest: rtl/manifest.yaml
   tb_manifest: tb/manifest.yaml
   fw_manifest: fw/manifest.yaml

   # OR auto-detect standard locations
   # ip/complex_ip/rtl/manifest.yaml
   # ip/complex_ip/tb/manifest.yaml
   # ip/complex_ip/fw/manifest.yaml


IP Class Diagram
~~~~~~~~~~~~~~~~

.. uml::
   :align: center
   :caption: IPManifest Structure

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   class IPManifest {
      +name: str
      +type: str
      +version: str
      +vendor: str
      +license: str
      +language: str
      +files: List[str]
      +binaries: Dict[str, str]
      +parameters: Dict[str, Any]
      +interfaces: List[Dict]
      --
      +get_rtl_files(): List[Path]
      +has_simulation_model(): bool
      +get_rtl_manifest(): RTLManifest
      +get_testbench_manifest(): TestbenchManifest
   }

   IPManifest ..> RTLManifest : may contain
   IPManifest ..> TestbenchManifest : may contain
   IPManifest ..> FirmwareManifest : may contain
   @enduml


Validation
----------

ALY validates manifests when loading them. Validation checks:

- Required fields are present
- Referenced files exist
- Dependencies are valid
- Type values are correct

Validation messages have severity levels:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Level
     - Description
   * - ``ERROR``
     - Fatal issues that prevent loading
   * - ``WARNING``
     - Non-fatal issues that should be addressed
   * - ``INFO``
     - Informational messages


File Resolution
---------------

File paths in manifests are resolved relative to the manifest location:

.. code-block:: text

   project/
   +-- rtl/
   |   +-- manifest.yaml      # Manifest location
   |   +-- core/
   |   |   +-- cpu.sv         # files: ["core/cpu.sv"]
   |   +-- include/           # includes: ["include"]


Glob patterns are expanded:

.. code-block:: yaml

   files:
     - "*.sv"           # All .sv files in same directory
     - "core/*.sv"      # All .sv files in core/
     - "**/*.sv"        # All .sv files recursively


Next Steps
----------

- :doc:`configuration` - Project configuration reference
- :doc:`commands/index` - CLI commands for working with manifests
- :doc:`api/index` - Python API for manifest handling
