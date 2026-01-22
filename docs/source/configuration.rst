=============
Configuration
=============

ALY uses a YAML-based configuration system with a clear hierarchy. This guide covers all configuration options.

.. contents::
   :local:
   :depth: 2

Configuration Files
-------------------

Project configuration lives in the ``.aly/`` directory with separate files for each domain:

.. code-block:: text

   .aly/
   +-- config.yaml         # Main project configuration
   +-- sim.yaml            # Simulation configuration
   +-- synth.yaml          # Synthesis configuration
   +-- lint.yaml           # Linting configuration
   +-- constraints.yaml    # Constraints configuration
   +-- fpga.yaml           # FPGA programming configuration
   +-- toolchains.yaml     # Firmware toolchains configuration

Each domain has its own configuration file that is loaded when needed. This modular approach keeps configurations organized and focused.


Configuration Structure
-----------------------

.. uml::
   :align: center
   :caption: Configuration Class Hierarchy

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   class ProjectConfig {
      +project: ProjectInfo
      +features: FeatureFlags
      +paths: PathsConfig
      +defaults: DefaultsConfig
      +simulation: SimConfig
      +synthesis: SynthConfig
      +lint: LintConfig
      +constraints: ConstraintsConfig
      +fpga: FPGAConfig
   }

   class ProjectInfo {
      +name: str
      +version: str
      +author: str
      +license: str
      +language: str
   }

   class FeatureFlags {
      +firmware: bool
      +ip: bool
      +constraints: bool
      +formal: bool
      +coverage: bool
   }

   class DefaultsConfig {
      +simulator: str
      +synthesizer: str
      +linter: str
   }

   ProjectConfig *-- ProjectInfo
   ProjectConfig *-- FeatureFlags
   ProjectConfig *-- DefaultsConfig
   @enduml


Project Information
-------------------

Basic project metadata:

.. code-block:: yaml

   # .aly/config.yaml
   project:
     name: my_soc
     version: 1.0.0
     author: Your Name
     license: Apache-2.0
     description: My System-on-Chip design
     language: systemverilog

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Required
     - Description
   * - ``name``
     - Yes
     - Project identifier (alphanumeric, underscores)
   * - ``version``
     - No
     - Semantic version (default: "1.0.0")
   * - ``author``
     - No
     - Project author or organization
   * - ``license``
     - No
     - License identifier (SPDX format)
   * - ``description``
     - No
     - Brief project description
   * - ``language``
     - No
     - Default HDL language (verilog, systemverilog, vhdl)


Feature Flags
-------------

Enable or disable project features:

.. code-block:: yaml

   features:
     firmware: true      # Enable firmware builds
     ip: true           # Enable IP management
     constraints: true  # Enable constraint management
     formal: false      # Enable formal verification
     coverage: false    # Enable coverage collection

Features affect which commands and configurations are available.


Path Configuration
------------------

Customize project directory structure:

.. code-block:: yaml

   paths:
     rtl: rtl              # RTL source directory
     testbench: tb         # Testbench directory
     firmware: fw          # Firmware directory
     ip: ip                # IP blocks directory
     constraints: constraints  # Constraints directory
     build: build          # Build output directory

All paths are relative to the project root.


Default Tools
-------------

Set default tools for each workflow:

.. code-block:: yaml

   defaults:
     simulator: xsim      # Default simulator
     synthesizer: vivado  # Default synthesizer
     linter: verilator    # Default linter


Simulation Configuration
------------------------

Configure simulation tools and options in ``.aly/sim.yaml``:

.. code-block:: yaml

   # .aly/sim.yaml
   default_tool: xsim
   language: systemverilog
   build_dir: build/sim
   waves: false
   verbosity: normal

   tools:
     xsim:
       bin: xsim
       vlog: xvlog
       xelab: xelab
       compile_opts:
         - -sv
         - -d SIMULATION
       elab_opts:
         - -debug typical
       run_opts:
         - -runall
       gui_opts:
         - -gui

     verilator:
       bin: verilator
       args:
         - --binary
         - --trace
         - -Wall
         - -Wno-fatal
         - --timing

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


Tool Options Reference
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Option
     - Description
   * - ``bin``
     - Path to main tool binary
   * - ``vlog``
     - Verilog/SV compiler (XSim, Questa)
   * - ``xelab``
     - Elaborator (XSim)
   * - ``vsim``
     - Simulator executable (Questa)
   * - ``vvp``
     - VVP runtime (Icarus)
   * - ``compile_opts``
     - Compilation flags
   * - ``elab_opts``
     - Elaboration flags
   * - ``run_opts``
     - Runtime flags
   * - ``gui_opts``
     - GUI mode flags
   * - ``args``
     - General arguments


Synthesis Configuration
-----------------------

Configure synthesis tools and targets in ``.aly/synth.yaml``:

.. code-block:: yaml

   # .aly/synth.yaml
   default_tool: vivado
   build_dir: build/synth

   # Cell libraries (for ASIC flows)
   libraries:
     sky130_hd:
       liberty: libs/sky130_fd_sc_hd__tt_025C_1v80.lib
       verilog: libs/sky130_fd_sc_hd.v
       lef: libs/sky130_fd_sc_hd.lef

   # Tool configurations
   tools:
     vivado:
       bin: vivado
       threads: 8
       batch_opts:
         - -mode
         - batch

     yosys:
       bin: yosys
       tech: generic
       script_ext: .ys

   # Synthesis targets
   targets:
     arty_a7:
       tool: vivado
       part: xc7a100tcsg324-1
       top: fpga_top
       constraints:
         - constraints/arty_a7.xdc
       options:
         strategy: Flow_PerfOptimized_high

     ice40:
       tool: yosys
       tech: ice40
       top: fpga_top


Synthesis Target Options
~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Option
     - Description
   * - ``tool``
     - Synthesis tool (vivado, yosys)
   * - ``part``
     - FPGA part number
   * - ``tech``
     - Technology target (Yosys: generic, ice40, ecp5, gowin)
   * - ``library``
     - Reference to cell library (ASIC)
   * - ``top``
     - Top-level module name
   * - ``constraints``
     - List of constraint files
   * - ``options``
     - Tool-specific options


Lint Configuration
------------------

Configure linting tools and rules in ``.aly/lint.yaml``:

.. code-block:: yaml

   # .aly/lint.yaml
   default_tool: verilator
   severity: warning

   tools:
     verilator:
       bin: verilator
       args:
         - --lint-only
         - -Wall
         - -Wno-fatal

     slang:
       bin: slang
       args:
         - --lint-only

   rules:
     categories:
       style: true
       synthesis: true
       simulation: false

     enable:
       - UNUSED
       - WIDTH

     disable:
       - DECLFILENAME

   waivers:
     - "ip/**/*.v"           # Waive vendor IP
     - "**/deprecated/**"    # Waive deprecated code


Constraints Configuration
-------------------------

Configure design constraints in ``.aly/constraints.yaml``:

.. code-block:: yaml

   # .aly/constraints.yaml
   default_target: arty_a7

   sets:
     arty_a7:
       target: xc7a100tcsg324-1
       files:
         - constraints/arty_a7/pins.xdc
         - constraints/arty_a7/timing.xdc

     nexys_a7:
       target: xc7a100tcsg324-1
       files:
         - constraints/nexys_a7/pins.xdc

   clocks:
     sys_clk:
       period: 10.0
       waveform: [0.0, 5.0]
       pin: E3

   io_defaults:
     standard: LVCMOS33
     drive: 12
     slew: SLOW


FPGA Configuration
------------------

Configure FPGA programming in ``.aly/fpga.yaml``:

.. code-block:: yaml

   # .aly/fpga.yaml
   default_board: arty_a7

   boards:
     arty_a7:
       part: xc7a100tcsg324-1
       programmer: hw_server
       bitstream: build/synth/vivado/fpga_top.bit

     nexys_a7:
       part: xc7a100tcsg324-1
       programmer: hw_server


Toolchain Configuration
-----------------------

Configure firmware toolchains in ``.aly/toolchains.yaml``:

.. code-block:: yaml

   # .aly/toolchains.yaml
   default: riscv64

   toolchains:
     riscv64:
       prefix: riscv64-unknown-elf-
       cc: gcc
       ld: ld
       as: as
       objcopy: objcopy
       objdump: objdump
       size: size

       # Default flags
       cflags:
         - -march=rv64imac
         - -mabi=lp64
         - -Wall
       asflags:
         - -march=rv64imac
       ldflags:
         - -nostartfiles

     arm:
       prefix: arm-none-eabi-
       cc: gcc
       ld: ld
       as: as
       objcopy: objcopy
       objdump: objdump
       size: size

       cflags:
         - -mcpu=cortex-m4
         - -mthumb
         - -Wall


Complete Example
----------------

Here's a complete main configuration file:

.. code-block:: yaml

   # .aly/config.yaml

   project:
     name: my_riscv_soc
     version: 1.0.0
     author: Mohamed Aly
     license: Apache-2.0
     language: systemverilog

   features:
     firmware: true
     ip: true
     constraints: true
     formal: false

   paths:
     rtl: rtl
     testbench: tb
     firmware: fw
     ip: ip
     constraints: constraints
     build: build

   defaults:
     simulator: xsim
     synthesizer: vivado
     linter: verilator

And a companion simulation configuration:

.. code-block:: yaml

   # .aly/sim.yaml

   default_tool: xsim
   waves: true
   build_dir: build/sim

   tools:
     xsim:
       bin: xsim
       vlog: xvlog
       xelab: xelab
       compile_opts: [-sv, -d SIMULATION]
       elab_opts: [-debug typical]
       run_opts: [-runall]

     verilator:
       bin: verilator
       args: [--binary, --trace, -Wall, --timing]


Environment Variables
---------------------

Override configuration with environment variables:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - Description
   * - ``ALY_PROJECT_ROOT``
     - Override project root detection
   * - ``ALY_CONFIG_FILE``
     - Custom config file path
   * - ``ALY_BUILD_DIR``
     - Override build directory
   * - ``VIVADO_HOME``
     - Vivado installation path
   * - ``VERILATOR_ROOT``
     - Verilator installation path


Next Steps
----------

- :doc:`manifest_system` - Component manifest reference
- :doc:`commands/index` - CLI command reference
- :doc:`examples` - Example configurations
