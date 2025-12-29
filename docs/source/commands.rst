Command Reference
=================

Built-in Commands
-----------------

aly init
~~~~~~~~

Initialize a new ALY project from a template.

.. code-block:: bash

   aly init [PATH] [--template TEMPLATE]

Options:
  * ``PATH`` - Project directory (default: current directory)
  * ``--template`` - Template to use (default: soc)
  * ``--list-templates`` - Show available templates

Templates:
  * ``soc`` - Full SoC project with RTL, firmware, verification
  * ``firmware-only`` - Firmware-only project

Example:

.. code-block:: bash

   aly init my-soc --template soc

aly info
~~~~~~~~

Display configuration and toolchain status.

.. code-block:: bash

   aly info

Shows:
  * Project root directory
  * Build directory location
  * RISC-V toolchain status
  * Vivado toolchain status

aly firmware
~~~~~~~~~~~~

Build RISC-V firmware from C and assembly sources.

.. code-block:: bash

   aly firmware [SOURCES...] [-o OUTPUT]

Options:
  * ``SOURCES`` - Specific files to build (default: all in firmware/)
  * ``-o, --output`` - Output directory (default: .aly_build/firmware)

Examples:

.. code-block:: bash

   # Build all firmware
   aly firmware

   # Build specific files
   aly firmware firmware/src/main.c

   # Custom output directory
   aly firmware -o build/fw

Output files:
  * ``.elf`` - Executable ELF binary
  * ``.bin`` - Raw binary
  * ``.mem`` - Verilog hex format (for $readmemh)
  * ``.lst`` - Disassembly listing

aly clean
~~~~~~~~~

Remove build artifacts.

.. code-block:: bash

   aly clean

Removes the entire ``.aly_build/`` directory.

aly version
~~~~~~~~~~~

Show ALY version information.

.. code-block:: bash

   aly version

Global Options
--------------

These options work with all commands:

.. code-block:: bash

   aly [OPTIONS] COMMAND

Options:
  * ``-v, --verbose`` - Increase verbosity (can repeat: -v, -vv, -vvv)
  * ``-q, --quiet`` - Suppress non-error output
  * ``-V, --version`` - Show version and exit
  * ``-h, --help`` - Show help and exit

Examples:

.. code-block:: bash

   # Verbose output
   aly -vv firmware

   # Quiet mode
   aly -q clean

   # Show help
   aly --help
   aly firmware --help

Extension Commands
------------------

Projects can define custom commands in ``.aly/commands.yml``.
See :doc:`extensions` for details.

Exit Codes
----------

ALY commands return:
  * ``0`` - Success
  * ``1`` - General error
  * ``130`` - Interrupted (Ctrl+C)
