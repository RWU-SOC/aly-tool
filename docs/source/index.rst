ALY Documentation
==================

Welcome to ALY (Advanced Logic Yieldflow) - a Python-based build and verification tool for RTL/SoC development.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   workflow_overview
   commands
   rtl_workflow
   extensions
   architecture
   api
   contributing
   changelog

What is ALY?
------------

ALY is a modern build and verification tool designed for RTL/SoC development. It provides:

* **RTL Workflow**: Simulate with XSIM/Questa/Verilator, synthesize with Vivado/Yosys
* **Firmware Build**: Integrated RISC-V firmware compilation and memory generation
* **Regression Testing**: Parallel test execution with multiple simulators
* **Project Templates**: Generate complete SoC project structures
* **Extension System**: Add custom commands and simulator backends
* **Pluggable Backends**: Support for multiple EDA tools via clean abstraction
* **Zero Magic**: Clean, readable Python code with clear architecture

Quick Start
-----------

Install ALY:

.. code-block:: bash

   pip install aly

Create a new project:

.. code-block:: bash

   aly init my-soc --template soc
   cd my-soc

Run simulation:

.. code-block:: bash

   aly sim --top soc_tb --tool xsim --waves

Build firmware:

.. code-block:: bash

   aly firmware

Run regression:

.. code-block:: bash

   aly regress --tool verilator -j 4

Why ALY?
--------

Compared to CMake or other build systems:

* **520 lines** of code vs 1000+ in CMake
* **Easy to debug** - it's just Python
* **RTL-specific** - built for SoC workflows
* **Extensible** - add commands without modifying core

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
