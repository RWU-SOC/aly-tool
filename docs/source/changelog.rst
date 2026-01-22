=========
Changelog
=========

All notable changes to ALY are documented here.

The format is based on `Keep a Changelog <https://keepachangelog.com/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/>`_.

[Unreleased]
------------

Added
~~~~~
- Comprehensive Sphinx documentation with PlantUML and Graphviz diagrams
- API reference documentation
- Command reference documentation
- Example workflows

[1.0.0] - 2025-01-22
--------------------

Added
~~~~~
- Initial release of ALY
- Project initialization with templates
- RTL manifest system with module dependencies
- Testbench manifest with test suites
- Firmware build system with GCC toolchain
- IP management for vendor and internal IP
- Simulation backends: XSim, Verilator, QuestaSim
- Synthesis backends: Vivado, Yosys
- Linting with Verilator
- Constraint management (XDC, PCF)
- FPGA programming support
- Configuration system with YAML files
- CLI with Typer framework

Changed
~~~~~~~
- N/A

Deprecated
~~~~~~~~~~
- N/A

Removed
~~~~~~~
- N/A

Fixed
~~~~~
- N/A

Security
~~~~~~~~
- N/A


Version History
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Version
     - Date
     - Highlights
   * - 1.0.0
     - 2025-01-22
     - Initial release


Migration Guides
----------------

Migrating to 1.0
~~~~~~~~~~~~~~~~

This is the initial release. No migration required.


Upgrade Notes
-------------

General Upgrade Process
~~~~~~~~~~~~~~~~~~~~~~~

1. Backup your project
2. Update ALY:

   .. code-block:: bash

      pip install --upgrade aly

3. Run validation:

   .. code-block:: bash

      aly config validate

4. Check for deprecation warnings
