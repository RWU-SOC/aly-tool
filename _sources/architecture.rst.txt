============
Architecture
============

This document describes ALY's internal architecture and design principles.

.. contents::
   :local:
   :class: toc-hidden
   :depth: 2

System Overview
---------------

ALY is designed as a modular, extensible tool for HDL development workflows.

.. uml::
   :align: center
   :caption: High-Level Architecture

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif
   skinparam componentStyle rectangle

   package "CLI Layer" {
      [Typer CLI] as cli
      [Command Handlers] as handlers
   }

   package "Core" {
      [Configuration] as config
      [Manifest System] as manifest
      [Template Engine] as templates
   }

   package "Backends" {
      [Simulator Backends] as sim
      [Synthesis Backends] as synth
      [Firmware Backend] as fw
   }

   package "External Tools" {
      [Vivado] as vivado
      [Yosys] as yosys
      [Verilator] as verilator
      [XSim] as xsim
      [QuestaSim] as questa
      [GCC] as gcc
   }

   cli --> handlers
   handlers --> config
   handlers --> manifest
   handlers --> templates

   handlers --> sim
   handlers --> synth
   handlers --> fw

   sim --> xsim
   sim --> verilator
   sim --> questa
   synth --> vivado
   synth --> yosys
   fw --> gcc
   @enduml


Module Structure
----------------

.. graphviz::
   :align: center
   :caption: Python Module Organization

   digraph modules {
      rankdir=TB;
      node [shape=box, style="rounded,filled", fontname="sans-serif"];
      edge [fontname="sans-serif"];

      subgraph cluster_aly {
         label="aly";
         style=filled;
         fillcolor="#f5f5f5";

         main [label="__main__.py\n(Entry point)", fillcolor="#e3f2fd"];
         commands [label="commands.py\n(CLI registration)", fillcolor="#e3f2fd"];
         util [label="util.py\n(Utilities)", fillcolor="#eceff1"];
         log [label="log.py\n(Logging)", fillcolor="#eceff1"];
         backends [label="backends.py\n(Backend registry)", fillcolor="#fff3e0"];
         configuration [label="configuration.py\n(Config loading)", fillcolor="#e8f5e9"];
      }

      subgraph cluster_app {
         label="aly.app";
         style=filled;
         fillcolor="#fafafa";

         app_main [label="main.py", fillcolor="#f3e5f5"];
         init [label="init.py", fillcolor="#f3e5f5"];
         simulate [label="simulate.py", fillcolor="#f3e5f5"];
         synthesize [label="synthesize.py", fillcolor="#f3e5f5"];
         lint [label="lint.py", fillcolor="#f3e5f5"];
         firmware [label="firmware.py", fillcolor="#f3e5f5"];
      }

      subgraph cluster_config {
         label="aly.config";
         style=filled;
         fillcolor="#fafafa";

         project_config [label="project_config.py", fillcolor="#e8f5e9"];
         models_init [label="models/__init__.py", fillcolor="#e8f5e9"];
      }

      main -> commands;
      commands -> app_main;
      app_main -> init;
      app_main -> simulate;
      app_main -> synthesize;
      app_main -> lint;
      app_main -> firmware;

      simulate -> backends;
      synthesize -> backends;
      lint -> backends;

      app_main -> configuration;
      configuration -> project_config;
      project_config -> models_init;
   }


Configuration System
--------------------

The configuration system uses a hierarchical loading mechanism.

.. uml::
   :align: center
   :caption: Configuration Loading Sequence

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   actor User
   participant CLI
   participant "ProjectConfig" as PC
   participant "YAML Parser" as YAML
   participant "Model Classes" as Models

   User -> CLI: aly <command>
   CLI -> PC: load()
   PC -> PC: find_project_root()
   PC -> YAML: parse config.yaml
   YAML --> PC: raw dict
   PC -> Models: from_dict()
   Models --> PC: typed config
   PC --> CLI: ProjectConfig
   CLI -> CLI: execute command
   @enduml


Configuration Class Hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. uml::
   :align: center
   :caption: Configuration Classes

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
      --
      +load(path): ProjectConfig
      +validate(): List[ValidationMessage]
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

   class PathsConfig {
      +rtl: str
      +testbench: str
      +firmware: str
      +ip: str
      +constraints: str
      +build: str
   }

   class SimConfig {
      +default_tool: str
      +build_dir: str
      +tools: Dict[str, SimToolConfig]
      +waves: bool
      +coverage: bool
   }

   class SynthConfig {
      +default_tool: str
      +build_dir: str
      +tools: Dict[str, Dict]
      +targets: Dict[str, SynthTargetConfig]
      +libraries: Dict[str, CellLibrary]
   }

   ProjectConfig *-- ProjectInfo
   ProjectConfig *-- FeatureFlags
   ProjectConfig *-- PathsConfig
   ProjectConfig *-- SimConfig
   ProjectConfig *-- SynthConfig
   @enduml




Unit Registry System
~~~~~~~~~~~~~~~~~~~~

ALY uses a unified unit registry that tracks individual components (modules, testbenches, builds) separately from their parent manifests. This enables efficient lookup and dependency resolution without requiring knowledge of the parent manifest.

.. uml::
   :align: center
   :caption: Unit Reference Architecture

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   class ProjectConfig {
      -_units: Dict[str, Dict[str, UnitRef]]
      -_components: Dict[str, Dict[str, Manifest]]
      --
      +get_rtl_module(name): UnitRef
      +get_testbench(name): UnitRef
      +get_firmware_build(name): UnitRef
      +get_package_unit(name): UnitRef
      +resolve_rtl_deps(unit): List[UnitRef]
      +resolve_package_deps(tb): List[UnitRef]
   }

   class UnitRef {
      +kind: str
      +name: str
      +manifest_type: str
      +manifest_name: str
      +manifest: Any
      +obj: Any
   }

   class RTLManifest {
      +modules: List[RTLModule]
      +packages: List[RTLPackage]
   }

   class RTLModule {
      +name: str
      +files: List[str]
      +dependencies: List[Dict]
   }

   class Testbench {
      +name: str
      +files: List[str]
      +dependencies: List[Dict]
   }

   ProjectConfig "1" *-- "*" UnitRef : contains
   ProjectConfig "1" *-- "*" RTLManifest : discovers
   RTLManifest "1" *-- "*" RTLModule : defines
   UnitRef --> RTLModule : obj
   UnitRef --> RTLManifest : manifest
   UnitRef --> Testbench : obj (for testbench units)
   @enduml

The unit registry provides several key capabilities:

**Direct Lookup**
   Components can be retrieved by name without knowing which manifest contains them:

   .. code-block:: python

      # Get RTL module from anywhere in the project
      ref = config.get_rtl_module("cpu_core")
      module = ref.obj          # RTLModule object
      manifest = ref.manifest   # Parent RTLManifest

**Dependency Resolution**
   Dependencies are resolved recursively with automatic cycle detection:

   .. code-block:: python

      # Resolve all RTL dependencies for a testbench
      deps = config.resolve_rtl_deps(testbench)
      for dep_ref in deps:
          module = dep_ref.obj
          files = dep_ref.manifest.get_files_for_module(module.name)

**Type Safety**
   Each unit type has dedicated accessor methods with proper typing:

   .. code-block:: python

      # Type-safe accessors
      rtl_modules = config.list_rtl_modules()      # List[str]
      testbenches = config.list_testbenches()      # List[str]
      fw_builds = config.list_firmware_builds()    # List[str]
      packages = config.list_packages()            # List[str]

**Manifest Context**
   Units maintain bidirectional references to their parent manifests for path resolution and file access:

   .. code-block:: python

      ref = config.get_rtl_module("alu")
      
      # Access module object
      module_name = ref.obj.name
      module_files = ref.obj.files
      
      # Access parent manifest for path resolution
      resolved_files = ref.manifest.get_files_for_module(ref.obj.name)

Unit Types
^^^^^^^^^^

The registry tracks four unit types:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Unit Kind
     - Source
     - Description
   * - ``rtl_module``
     - RTL manifests
     - Individual synthesizable modules
   * - ``testbench``
     - Testbench manifests
     - Individual simulation testbenches
   * - ``firmware_build``
     - Firmware manifests
     - Individual firmware build configurations
   * - ``package``
     - RTL manifests
     - Named SystemVerilog packages

Discovery Process
^^^^^^^^^^^^^^^^^

Units are registered during manifest discovery:

.. uml::
   :align: center
   :caption: Unit Registration Flow

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   start
   :Discover manifest.yaml;
   :Load and parse manifest;
   :Register manifest in _components;
   
   if (Manifest type?) then (rtl)
      :Extract modules list;
      while (For each module) is (more)
         :Create UnitRef;
         :Register in _units["rtl_module"];
      endwhile (done)
      
      :Extract packages list;
      while (For each package) is (more)
         :Create UnitRef;
         :Register in _units["package"];
      endwhile (done)
      
   else (testbench)
      :Extract testbenches list;
      while (For each testbench) is (more)
         :Create UnitRef;
         :Register in _units["testbench"];
      endwhile (done)
      
   else (firmware)
      :Extract builds list;
      while (For each build) is (more)
         :Create UnitRef;
         :Register in _units["firmware_build"];
      endwhile (done)
   endif
   
   stop
   @enduml


Manifest Validation
~~~~~~~~~~~~~~~~~~~

ALY validates manifests at load time to catch configuration errors early.

.. uml::
   :align: center
   :caption: Manifest Validation Process

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   start
   :Load YAML file;
   
   :Parse YAML structure;
   
   if (Valid YAML?) then (no)
      :Return syntax error;
      stop
   endif
   
   :Validate required fields;
   
   if (All required fields present?) then (no)
      :Return missing field error;
      stop
   endif
   
   :Validate field types;
   
   if (All types correct?) then (no)
      :Return type error;
      stop
   endif
   
   :Validate cross-references;
   note right
      - Dependencies exist
      - File paths are valid
      - Module names unique
   end note
   
   if (References valid?) then (no)
      :Return reference error;
      stop
   endif
   
   :Create manifest object;
   :Return success;
   stop
   @enduml

Validation checks include:

- **Syntax validation**: YAML structure is well-formed
- **Schema validation**: Required fields are present with correct types
- **Reference validation**: Dependencies reference existing components
- **Path validation**: File paths exist relative to manifest location
- **Uniqueness validation**: Module/build names are unique within manifest
- **Type compatibility**: Dependency types match referenced component types

Validation errors are reported with the manifest file path, line number (when available), and a descriptive error message to help users quickly locate and fix issues.


Backend System
--------------

Backends abstract tool-specific implementations.

.. uml::
   :align: center
   :caption: Simulator Backend Architecture

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   interface SimulatorBackend {
      +compile(sources, options): bool
      +elaborate(top, options): bool
      +simulate(options): SimResult
      +cleanup(): void
   }

   class XSimBackend {
      -config: SimConfig
      -build_dir: Path
      --
      +compile(sources, options): bool
      +elaborate(top, options): bool
      +simulate(options): SimResult
      -run_xvlog(files): bool
      -run_xelab(top): bool
      -run_xsim(snapshot): SimResult
   }

   class VerilatorBackend {
      -config: SimConfig
      -build_dir: Path
      --
      +compile(sources, options): bool
      +elaborate(top, options): bool
      +simulate(options): SimResult
      -generate_makefile(): void
      -build_executable(): bool
   }

   class QuestaBackend {
      -config: SimConfig
      -build_dir: Path
      --
      +compile(sources, options): bool
      +elaborate(top, options): bool
      +simulate(options): SimResult
      -run_vlog(files): bool
      -run_vsim(top): SimResult
   }

   SimulatorBackend <|.. XSimBackend
   SimulatorBackend <|.. VerilatorBackend
   SimulatorBackend <|.. QuestaBackend
   @enduml


Synthesis Backend Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. uml::
   :align: center
   :caption: Synthesis Backend Architecture

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   interface SynthBackend {
      +synthesize(sources, top, options): bool
      +implement(options): bool
      +generate_bitstream(): Path
      +get_reports(): Dict[str, Path]
   }

   class VivadoBackend {
      -config: SynthConfig
      -target: SynthTargetConfig
      -build_dir: Path
      --
      +synthesize(sources, top, options): bool
      +implement(options): bool
      +generate_bitstream(): Path
      -generate_tcl_script(): Path
      -run_vivado(script): bool
   }

   class YosysBackend {
      -config: SynthConfig
      -target: SynthTargetConfig
      -build_dir: Path
      --
      +synthesize(sources, top, options): bool
      +implement(options): bool
      +generate_bitstream(): Path
      -generate_ys_script(): Path
      -run_yosys(script): bool
      -run_nextpnr(): bool
   }

   SynthBackend <|.. VivadoBackend
   SynthBackend <|.. YosysBackend
   @enduml


Command Processing
------------------

Commands are processed through the Typer CLI framework.

.. uml::
   :align: center
   :caption: Command Processing Flow

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   start
   :Parse CLI arguments;
   :Load project config;

   if (Config valid?) then (no)
      :Show error;
      stop
   endif

   :Load manifests;

   switch (Command)
   case (simulate)
      :Resolve RTL dependencies;
      :Select simulator backend;
      :Compile sources;
      :Elaborate design;
      :Run simulation;
   case (synth)
      :Select synthesis target;
      :Select synth backend;
      :Generate TCL/YS script;
      :Run synthesis;
      :Generate reports;
   case (lint)
      :Collect source files;
      :Run linter;
      :Parse output;
      :Format results;
   case (firmware)
      :Load toolchain config;
      :Compile sources;
      :Link objects;
      :Generate outputs;
   endswitch

   :Display results;
   stop
   @enduml


Error Handling
~~~~~~~~~~~~~~

ALY uses a structured error handling approach to provide clear, actionable feedback.

.. list-table:: Error Categories
   :header-rows: 1
   :widths: 20 40 40

   * - Error Type
     - Description
     - Example
   * - Configuration Error
     - Invalid or missing configuration files
     - ``config.yaml not found in project root``
   * - Manifest Error
     - Invalid manifest structure or references
     - ``Module 'alu' referenced but not found``
   * - Dependency Error
     - Missing or circular dependencies
     - ``Circular dependency detected: cpu → alu → cpu``
   * - Tool Error
     - External tool execution failure
     - ``XSim compilation failed: syntax error in counter.sv``
   * - File Error
     - Missing or inaccessible files
     - ``File not found: rtl/counter.sv``
   * - Backend Error
     - Backend-specific errors
     - ``Vivado backend requires --part argument``

Error messages include:

- **Context**: Which file or component caused the error
- **Location**: Line number or path when available
- **Description**: Clear explanation of what went wrong
- **Suggestion**: Recommended fix or next steps

Example error output:

.. code-block:: text

   Error: Manifest validation failed
   File: testbench/tb_cpu/manifest.yaml
   Line: 12
   Issue: Dependency 'cpu_core' not found
   
   The testbench references RTL module 'cpu_core' but this module
   does not exist in rtl/manifest.yaml.
   
   Suggestion: Add cpu_core to rtl/manifest.yaml or check the spelling.


Dependency Resolution
---------------------

ALY resolves module dependencies through a graph-based approach.

.. graphviz::
   :align: center
   :caption: Dependency Resolution Example

   digraph deps {
      rankdir=BT;
      node [shape=component, style=filled, fillcolor="#e8f5e9", fontname="sans-serif"];
      edge [fontname="sans-serif"];

      tb [label="tb_cpu\n(testbench)", fillcolor="#fce4ec"];
      cpu [label="cpu_core"];
      alu [label="alu"];
      regfile [label="regfile"];
      decoder [label="decoder"];
      fw [label="boot.hex\n(firmware)", fillcolor="#f3e5f5"];
      pkg [label="cpu_pkg\n(package)", fillcolor="#e0f7fa"];

      tb -> cpu [label="deps (type: rtl)"];
      tb -> fw [label="deps (type: firmware)"];
      cpu -> alu [label="deps (type: rtl)"];
      cpu -> regfile [label="deps (type: rtl)"];
      cpu -> decoder [label="deps (type: rtl)"];
      decoder -> alu [label="deps (type: rtl)"];
      cpu -> pkg [style=dashed, label="uses"];
      alu -> pkg [style=dashed, label="uses"];
   }


Resolution Algorithm
~~~~~~~~~~~~~~~~~~~~

.. uml::
   :align: center
   :caption: Dependency Resolution Algorithm

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   start
   :Get target module/testbench;
   :Initialize visited set;
   :Initialize ordered list;

   while (Unvisited dependencies?) is (yes)
      :Get next dependency;

      if (Already visited?) then (yes)
         :Skip (cycle check);
      else (no)
         :Mark as visited;
         :Recursively resolve its deps;
         :Add to ordered list;
      endif
   endwhile (no)

   :Return ordered list;
   note right: Files are ordered\nfor correct compilation

   stop
   @enduml


File Organization
-----------------

.. code-block:: text

   aly-tool/
   +-- src/
   |   +-- aly/
   |       +-- __init__.py          # Package init
   |       +-- __main__.py          # Entry point
   |       +-- commands.py          # CLI command registration
   |       +-- configuration.py     # Config loading utilities
   |       +-- backends.py          # Backend registry
   |       +-- util.py              # Utility functions
   |       +-- log.py               # Logging setup
   |       |
   |       +-- app/                 # CLI command implementations
   |       |   +-- main.py          # Main app
   |       |   +-- init.py          # Project init
   |       |   +-- simulate.py      # Simulation commands
   |       |   +-- synthesize.py    # Synthesis commands
   |       |   +-- lint.py          # Linting commands
   |       |   +-- firmware.py      # Firmware commands
   |       |   +-- program.py       # FPGA programming
   |       |   +-- config.py        # Config commands
   |       |   +-- rtl.py           # RTL management
   |       |   +-- ip.py            # IP management
   |       |   +-- constraints.py   # Constraint management
   |       |
   |       +-- config/              # Configuration system
   |       |   +-- __init__.py
   |       |   +-- project_config.py
   |       |   +-- models/          # Data model classes
   |       |       +-- __init__.py
   |       |       +-- core.py      # Core config models
   |       |       +-- rtl.py       # RTL manifest
   |       |       +-- testbench.py # Testbench manifest
   |       |       +-- firmware.py  # Firmware manifest
   |       |       +-- ip.py        # IP manifest
   |       |       +-- tools.py     # Tool configs
   |       |       +-- helpers.py   # Helper classes
   |       |
   |       +-- sim_xsim.py          # XSim backend
   |       +-- sim_verilator.py     # Verilator backend
   |       +-- sim_questa.py        # QuestaSim backend
   |       +-- synth_vivado.py      # Vivado backend
   |       +-- synth_yosys.py       # Yosys backend
   |       +-- fw_gcc.py            # GCC firmware backend
   |       |
   |       +-- templates/           # Project templates
   |           +-- loader.py        # Template loader
   |           +-- basic/           # Basic template
   |           +-- soc/             # SoC template
   |
   +-- docs/                        # Documentation
   +-- tests/                       # Test suite


Design Principles
-----------------

1. **Modularity**: Each component is self-contained and testable
2. **Extensibility**: New backends can be added without modifying core
3. **Configuration-Driven**: Behavior controlled through YAML configuration
4. **Tool Abstraction**: Unified interface regardless of underlying tool
5. **Manifest-Based**: Components described declaratively


Extension Points
----------------

.. uml::
   :align: center
   :caption: Extension Points

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   package "Core (Fixed)" {
      [CLI Framework]
      [Configuration System]
      [Manifest Parser]
   }

   package "Extensible" {
      [Simulator Backends]
      [Synthesis Backends]
      [Lint Backends]
      [Templates]
   }

   package "External" {
      [Custom Scripts]
      [Hooks]
      [Plugins]
   }

   [CLI Framework] --> [Simulator Backends]
   [CLI Framework] --> [Synthesis Backends]
   [Configuration System] --> [Simulator Backends]
   [Configuration System] --> [Synthesis Backends]

   [Simulator Backends] ..> [Custom Scripts] : invoke
   [Synthesis Backends] ..> [Custom Scripts] : invoke
   @enduml


Next Steps
----------

- :doc:`api/index` - Python API reference
- :doc:`contributing` - Contributing guidelines
