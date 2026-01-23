============
Installation
============

This guide covers installing ALY and its dependencies.

Requirements
------------

**Python**
   Python 3.9 or higher is required.

**External Tools** (optional, depending on workflow):

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Tool
     - Purpose
     - Installation
   * - Vivado
     - Xilinx synthesis/simulation
     - `Xilinx Downloads <https://www.xilinx.com/support/download.html>`_
   * - Yosys
     - Open-source synthesis
     - ``apt install yosys`` or `YosysHQ <https://github.com/YosysHQ/yosys>`_
   * - Verilator
     - Fast RTL simulation/linting
     - ``apt install verilator`` or `Verilator <https://verilator.org/>`_
   * - ModelSim
     - RTL simulation
     - `ModelSim <https://www.altera.com/downloads/simulation-tools/modelsim-fpgas-standard-edition-software-version-20-1-1/>`_
   * - QuestaSim
     - Commercial simulation
     - Siemens EDA
   * - RISC-V GCC
     - Firmware compilation
     - ``apt install gcc-riscv64-unknown-elf``

Installation Methods
--------------------

From PyPI (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install aly-tool

From Source
~~~~~~~~~~~

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/RWU-SOC/aly-tool.git
   cd aly-tool

   # Install in development mode
   pip install -e .

   # Or install with development dependencies
   pip install -e ".[dev]"

Verify Installation
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Check version
   aly --version

   # List available commands
   aly --help


Environment Setup
-----------------

Tool Paths
~~~~~~~~~~

ALY automatically detects tools in your ``PATH``. You can also configure explicit paths in ``.aly/config.yaml``:

.. code-block:: yaml

   simulation:
     tools:
       xsim:
         bin: /opt/Xilinx/Vivado/2024.1/bin/xsim
       verilator:
         bin: /usr/local/bin/verilator

   synthesis:
     tools:
       vivado:
         bin: /opt/Xilinx/Vivado/2024.1/bin/vivado
       yosys:
         bin: /usr/bin/yosys


Project Structure
-----------------

After installation, you can create a new project:

.. code-block:: bash

   aly init my_project --template basic

This creates the following structure:

.. code-block:: text

   my_project/
   +-- .aly/                    # ALY configuration
   |   +-- config.yaml          # Project configuration
   +-- rtl/                     # RTL source files
   |   +-- manifest.yaml        # RTL manifest
   +-- tb/                      # Testbenches
   |   +-- manifest.yaml        # Testbench manifest
   +-- fw/                      # Firmware (optional)
   +-- constraints/             # Design constraints
   +-- build/                   # Build outputs


Next Steps
----------

- :doc:`quickstart` - Create and simulate your first design
- :doc:`concepts` - Understand ALY's core concepts
- :doc:`configuration` - Configure your project
