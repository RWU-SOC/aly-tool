.. ALY documentation master file

===================================
ALY - Advanced Logic Yieldflow
===================================

**ALY** is a comprehensive HDL/FPGA development tool that streamlines the entire hardware design workflow from RTL development through simulation, synthesis, and FPGA programming.

.. image:: https://img.shields.io/badge/License-Apache_2.0-blue.svg
   :target: https://opensource.org/licenses/Apache-2.0
   :alt: License

.. graphviz::
   :align: center

   digraph overview {
      rankdir=LR;
      node [shape=box, style="rounded,filled", fontname="sans-serif"];
      edge [fontname="sans-serif"];

      RTL [label="RTL Design", fillcolor="#e1f5fe"];
      Sim [label="Simulation", fillcolor="#fff3e0"];
      Synth [label="Synthesis", fillcolor="#f3e5f5"];
      FPGA [label="FPGA", fillcolor="#e8f5e9"];

      RTL -> Sim -> Synth -> FPGA;
   }

Key Features
------------

- **Manifest-Based Project Management**: YAML manifests for RTL, testbench, firmware, and IP components
- **Multi-Tool Support**: Works with Vivado, Yosys, Verilator, QuestaSim, and more
- **Unified CLI**: Single command-line interface for all development tasks
- **Template System**: Quick project scaffolding with customizable templates
- **Hierarchical Configuration**: Project-wide settings with per-component overrides

Getting Started
---------------

.. code-block:: bash

   # Install ALY
   pip install aly-tool

   # Initialize a new project
   aly init my_project --template basic

   # Run simulation
   aly sim --top my_testbench

   # Synthesize design
   aly synth --target arty_a7

Quick Navigation
----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   concepts

.. toctree::
   :maxdepth: 2
   :caption: Configuration

   configuration
   manifest_system
   templates
   constraints

.. toctree::
   :maxdepth: 2
   :caption: Workflows

   simulation
   synthesis
   linting
   ip_management

.. toctree::
   :maxdepth: 2
   :caption: Reference

   commands/index
   api/index
   architecture
   examples

.. toctree::
   :maxdepth: 1
   :caption: Project

   contributing
   changelog
   license


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
