=============
API Reference
=============

This section documents ALY's Python API for programmatic access.

.. contents::
   :local:
   :depth: 2

Overview
--------

ALY's API is organized into modules:

.. graphviz::
   :align: center
   :caption: API Module Structure

   digraph api {
      rankdir=TB;
      node [shape=box, style="rounded,filled", fontname="sans-serif"];

      aly [label="aly", fillcolor="#e3f2fd"];

      config [label="aly.config", fillcolor="#e8f5e9"];
      models [label="aly.config.models", fillcolor="#c8e6c9"];
      backends [label="aly.backends", fillcolor="#fff3e0"];
      app [label="aly.app", fillcolor="#f3e5f5"];

      aly -> config;
      aly -> backends;
      aly -> app;
      config -> models;
   }


Configuration API
-----------------

ProjectConfig
~~~~~~~~~~~~~

.. autoclass:: aly.config.ProjectConfig
   :members:
   :show-inheritance:

The main configuration class for loading and accessing project settings.

**Example:**

.. code-block:: python

   from aly.config import ProjectConfig

   # Load project configuration
   config = ProjectConfig.load()

   # Access project info
   print(f"Project: {config.project.name}")
   print(f"Version: {config.project.version}")

   # Get simulation config
   sim_config = config.simulation
   print(f"Default simulator: {sim_config.default_tool}")


Model Classes
-------------

RTLManifest
~~~~~~~~~~~

.. py:class:: aly.config.models.RTLManifest

   RTL component manifest.

   .. py:attribute:: name
      :type: str

      Manifest name

   .. py:attribute:: type
      :type: str

      Must be "rtl"

   .. py:attribute:: modules
      :type: List[RTLModule]

      List of RTL modules

   .. py:attribute:: packages
      :type: List[RTLPackage]

      SystemVerilog packages

   .. py:method:: load(path: Path) -> RTLManifest
      :classmethod:

      Load manifest from YAML file.

   .. py:method:: get_module(name: str) -> Optional[RTLModule]

      Get module by name.

   .. py:method:: get_all_files() -> List[Path]

      Get all RTL source files.

**Example:**

.. code-block:: python

   from pathlib import Path
   from aly.config.models import RTLManifest

   # Load RTL manifest
   manifest = RTLManifest.load(Path("rtl/manifest.yaml"))

   # Iterate modules
   for module in manifest.modules:
       print(f"Module: {module.name}")
       for f in module.get_files():
           print(f"  - {f}")


RTLModule
~~~~~~~~~

.. py:class:: aly.config.models.RTLModule

   Single RTL module definition.

   .. py:attribute:: name
      :type: str

      Module identifier

   .. py:attribute:: top
      :type: str

      Top-level module name

   .. py:attribute:: files
      :type: List[str]

      Source file paths/patterns

   .. py:attribute:: deps
      :type: List[str]

      Dependencies on other modules

   .. py:method:: get_files() -> List[Path]

      Resolve and return all source files.

   .. py:method:: resolve_files(manifest_dir: Path) -> List[Path]

      Resolve files relative to manifest directory.


TestbenchManifest
~~~~~~~~~~~~~~~~~

.. py:class:: aly.config.models.TestbenchManifest

   Testbench manifest for simulation.

   .. py:attribute:: name
      :type: str

      Manifest name

   .. py:attribute:: testbenches
      :type: List[Testbench]

      Testbench definitions

   .. py:attribute:: test_suites
      :type: List[TestSuite]

      Test suite groupings

   .. py:method:: load(path: Path) -> TestbenchManifest
      :classmethod:

      Load from YAML file.

   .. py:method:: get_testbench(name: str) -> Optional[Testbench]

      Get testbench by name.


Testbench
~~~~~~~~~

.. py:class:: aly.config.models.Testbench

   Single testbench definition.

   .. py:attribute:: name
      :type: str

      Testbench identifier

   .. py:attribute:: top
      :type: str

      Top module name

   .. py:attribute:: files
      :type: List[str]

      Testbench source files

   .. py:attribute:: rtl_deps
      :type: List[str]

      RTL module dependencies

   .. py:attribute:: fw_deps
      :type: List[str]

      Firmware dependencies

   .. py:attribute:: timeout
      :type: Optional[str]

      Simulation timeout


FirmwareManifest
~~~~~~~~~~~~~~~~

.. py:class:: aly.config.models.FirmwareManifest

   Firmware build manifest.

   .. py:attribute:: name
      :type: str

      Manifest name

   .. py:attribute:: toolchain
      :type: Toolchain

      Compiler toolchain config

   .. py:attribute:: builds
      :type: List[FirmwareBuild]

      Build definitions

   .. py:method:: load(path: Path) -> FirmwareManifest
      :classmethod:

      Load from YAML file.

   .. py:method:: get_build(name: str) -> Optional[FirmwareBuild]

      Get build by name.


IPManifest
~~~~~~~~~~

.. py:class:: aly.config.models.IPManifest

   Vendor IP block manifest.

   .. py:attribute:: name
      :type: str

      IP name

   .. py:attribute:: vendor
      :type: str

      Vendor name

   .. py:attribute:: version
      :type: str

      IP version

   .. py:attribute:: files
      :type: List[str]

      RTL source files

   .. py:attribute:: binaries
      :type: Dict[str, str]

      Precompiled models

   .. py:attribute:: parameters
      :type: Dict[str, Any]

      Configurable parameters

   .. py:method:: load(path: Path) -> IPManifest
      :classmethod:

      Load from YAML file.

   .. py:method:: get_rtl_files() -> List[Path]

      Get RTL source files.

   .. py:method:: has_simulation_model() -> bool

      Check for precompiled simulation model.


Backend API
-----------

Backends provide tool abstraction for simulation and synthesis.

.. uml::
   :align: center
   :caption: Backend Class Hierarchy

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   interface SimulatorBackend {
      +compile(sources, options)
      +elaborate(top, options)
      +simulate(options)
   }

   interface SynthBackend {
      +synthesize(sources, top, options)
      +implement(options)
      +generate_bitstream()
   }

   class XSimBackend
   class QuestaBackend
   class VerilatorBackend

   class VivadoBackend
   class YosysBackend

   SimulatorBackend <|.. XSimBackend
   SimulatorBackend <|.. QuestaBackend
   SimulatorBackend <|.. VerilatorBackend

   SynthBackend <|.. VivadoBackend
   SynthBackend <|.. YosysBackend
   @enduml


SimulatorBackend
~~~~~~~~~~~~~~~~

Base interface for simulation backends.

.. py:class:: aly.backends.SimulatorBackend

   Abstract base for simulator backends.

   .. py:method:: compile(sources: List[Path], options: Dict) -> bool
      :abstractmethod:

      Compile HDL sources.

   .. py:method:: elaborate(top: str, options: Dict) -> bool
      :abstractmethod:

      Elaborate design hierarchy.

   .. py:method:: simulate(options: Dict) -> SimResult
      :abstractmethod:

      Run simulation.


SynthBackend
~~~~~~~~~~~~

Base interface for synthesis backends.

.. py:class:: aly.backends.SynthBackend

   Abstract base for synthesis backends.

   .. py:method:: synthesize(sources: List[Path], top: str, options: Dict) -> bool
      :abstractmethod:

      Run synthesis.

   .. py:method:: implement(options: Dict) -> bool
      :abstractmethod:

      Run implementation (place & route).

   .. py:method:: generate_bitstream() -> Path
      :abstractmethod:

      Generate programming file.


Utility Functions
-----------------

Logging
~~~~~~~

.. py:module:: aly.log

.. py:function:: get_logger(name: str) -> Logger

   Get a configured logger.

   :param name: Logger name
   :return: Configured logger instance

.. py:function:: setup_logging(level: str = "INFO")

   Configure logging for CLI usage.

   :param level: Log level (DEBUG, INFO, WARNING, ERROR)


Configuration Utilities
~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: aly.configuration

.. py:function:: find_project_root(start: Path = None) -> Optional[Path]

   Find project root by looking for .aly directory.

   :param start: Starting directory (default: current directory)
   :return: Project root path or None


Template System
~~~~~~~~~~~~~~~

.. py:module:: aly.templates

.. py:class:: TemplateLoader

   Load and render project templates.

   .. py:method:: list_templates() -> List[TemplateInfo]
      :classmethod:

      List available templates.

   .. py:method:: load(name: str) -> TemplateLoader

      Load template by name.

   .. py:method:: render(output_dir: Path, variables: Dict)

      Render template to output directory.


Usage Examples
--------------

Loading a Project
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from aly.config import ProjectConfig
   from aly.configuration import find_project_root

   # Find and load project
   root = find_project_root()
   if root:
       config = ProjectConfig.load(root)
       print(f"Loaded project: {config.project.name}")

Running Simulation
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from aly.config import ProjectConfig
   from aly.config.models import RTLManifest, TestbenchManifest
   from aly.sim_xsim import XSimBackend

   # Load configuration
   config = ProjectConfig.load()

   # Load manifests
   rtl = RTLManifest.load(Path("rtl/manifest.yaml"))
   tb = TestbenchManifest.load(Path("tb/manifest.yaml"))

   # Get testbench
   testbench = tb.get_testbench("tb_counter")

   # Collect sources
   sources = []
   for dep in testbench.rtl_deps:
       module = rtl.get_module(dep)
       sources.extend(module.get_files())
   sources.extend(testbench.get_files())

   # Run simulation
   backend = XSimBackend(config.simulation)
   backend.compile(sources, {"waves": True})
   backend.elaborate(testbench.top, {})
   result = backend.simulate({"timeout": "1ms"})

   print(f"Simulation {'passed' if result.passed else 'failed'}")


Programmatic Synthesis
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from aly.config import ProjectConfig
   from aly.config.models import RTLManifest
   from aly.synth_vivado import VivadoBackend

   # Load configuration
   config = ProjectConfig.load()
   rtl = RTLManifest.load(Path("rtl/manifest.yaml"))

   # Get target configuration
   target = config.synthesis.get_target("arty_a7")

   # Collect all RTL files
   sources = rtl.get_all_files()

   # Run synthesis
   backend = VivadoBackend(config.synthesis)
   backend.synthesize(
       sources=sources,
       top=target.top,
       part=target.part,
       constraints=target.constraints
   )


Next Steps
----------

- :doc:`../commands/index` - CLI reference
- :doc:`../architecture` - Internal architecture
- :doc:`../examples` - More examples
