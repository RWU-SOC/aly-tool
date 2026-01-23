=======
Linting
=======

This guide covers RTL linting and static analysis.

.. contents::
   :local:
   :class: toc-hidden
   :depth: 2

Overview
--------

ALY supports multiple linting backends:

.. graphviz::
   :align: center
   :caption: Lint Backends

   digraph lint {
      rankdir=LR;
      node [shape=box, style="rounded,filled", fontname="sans-serif"];

      aly [label="aly lint", fillcolor="#e3f2fd"];

      verilator [label="Verilator\n(Lint mode)", fillcolor="#e8f5e9"];
      slang [label="Slang\n(SV parser)", fillcolor="#fff3e0"];

      aly -> verilator;
      aly -> slang;
   }


Basic Usage
-----------

.. code-block:: bash

   # Lint specific module (--module is required when no files given)
   aly lint --module cpu_core

   # Use specific linter
   aly lint --module cpu_core --tool slang

   # Lint specific files
   aly lint rtl/cpu.sv rtl/alu.sv

   # Errors only (suppress warnings)
   aly lint --module cpu_core --no-warnings


Lint Flow
---------

.. uml::
   :align: center
   :caption: Lint Execution Flow

   @startuml
   skinparam backgroundColor transparent
   skinparam defaultFontName sans-serif

   start
   :Load RTL manifest;
   :Collect source files;

   if (Module filter?) then (yes)
      :Filter to specified module;
   endif

   :Apply waivers;
   :Run linter;
   :Parse output;
   :Format results;

   if (Errors found?) then (yes)
      :Report errors;
      :Exit with error code;
   else (no)
      :Report success;
   endif
   stop
   @enduml


Configuration
-------------

Configure linting in ``.aly/config.yaml``:

.. code-block:: yaml

   lint:
     default_tool: verilator
     severity: warning

     tools:
       verilator:
         bin: verilator
         args:
           - --lint-only
           - -Wall
           - -Wno-fatal
           - -Wno-DECLFILENAME

       slang:
         bin: slang
         args:
           - --lint-only
           - -Weverything

     rules:
       categories:
         style: true
         synthesis: true
         simulation: false

       enable:
         - UNUSED
         - WIDTH
         - PINMISSING

       disable:
         - DECLFILENAME
         - VARHIDDEN

     waivers:
       - "ip/**/*.v"
       - "**/deprecated/**"


Lint Rules
----------

Verilator Rules
~~~~~~~~~~~~~~~

Common Verilator warnings:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Rule
     - Description
   * - ``UNUSED``
     - Unused signal or variable
   * - ``UNDRIVEN``
     - Signal never driven
   * - ``WIDTH``
     - Width mismatch in operations
   * - ``PINMISSING``
     - Missing port connection
   * - ``CASEINCOMPLETE``
     - Case statement not fully covered
   * - ``LATCH``
     - Inferred latch (usually unintended)
   * - ``MULTIDRIVEN``
     - Signal driven from multiple blocks
   * - ``BLKSEQ``
     - Blocking assignment in sequential block
   * - ``COMBDLY``
     - Delayed assignment in combinational block

Enable/disable specific rules:

.. code-block:: yaml

   lint:
     tools:
       verilator:
         args:
           - --lint-only
           - -Wall
           - -Wno-DECLFILENAME
           - -Wno-UNUSED


Rule Categories
~~~~~~~~~~~~~~~

Organize rules by category:

.. code-block:: yaml

   lint:
     rules:
       categories:
         style: true         # Coding style rules
         synthesis: true     # Synthesis-related checks
         simulation: false   # Simulation-only checks
         naming: true        # Naming conventions


Waivers
-------

Exclude files or patterns from linting:

.. code-block:: yaml

   lint:
     waivers:
       # Vendor IP - not under our control
       - "ip/**/*.v"
       - "ip/**/*.sv"

       # Generated code
       - "**/generated/**"

       # Legacy code (to be refactored)
       - "rtl/legacy/**"

       # Testbench-only files
       - "**/*_tb.sv"


Inline Waivers
~~~~~~~~~~~~~~

Disable warnings in code:

.. code-block:: systemverilog

   // verilator lint_off UNUSED
   logic unused_signal;
   // verilator lint_on UNUSED

   /* verilator lint_off WIDTH */
   assign narrow = wide;  // Intentional truncation
   /* verilator lint_on WIDTH */


Output
------

The lint output shows errors and warnings in a unified format:

.. code-block:: text

   rtl/cpu_core.sv:42: warning: Signal 'debug_out' is not used [-WUNUSED]
   rtl/alu.sv:15: warning: Width mismatch: 8 bits vs 16 bits [-WWIDTH]
   rtl/decoder.sv:88: error: Case statement not fully covered [-WCASEINCOMPLETE]

   === Summary ===
   Duration: 1.23s
   Errors: 1
   Warnings: 2


Severity Levels
---------------

Control warning display:

.. code-block:: bash

   # Show errors and warnings (default)
   aly lint --module cpu_core

   # Show only errors (suppress warnings)
   aly lint --module cpu_core --no-warnings

Severity hierarchy:

1. ``error`` - Must be fixed (always shown)
2. ``warning`` - Should be fixed (hidden with --no-warnings)


CI Integration
--------------

GitHub Actions
~~~~~~~~~~~~~~

.. code-block:: yaml

   # .github/workflows/lint.yml
   name: Lint RTL

   on: [push, pull_request]

   jobs:
     lint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4

         - name: Install Verilator
           run: sudo apt-get install -y verilator

         - name: Install ALY
           run: pip install aly-tool

         - name: Run lint
           run: aly lint --module cpu_core


Pre-commit Hook
~~~~~~~~~~~~~~~

.. code-block:: yaml

   # .pre-commit-config.yaml
   repos:
     - repo: local
       hooks:
         - id: aly-lint
           name: ALY Lint
           entry: aly lint --module cpu_core --no-warnings
           language: system
           files: \.(sv|v)$
           pass_filenames: false


Common Patterns
---------------

Avoiding Warnings
~~~~~~~~~~~~~~~~~

**Unused signals:**

.. code-block:: systemverilog

   // Bad - generates warning
   logic unused_sig;

   // Good - explicitly mark as unused
   logic unused_sig /* verilator lint_off UNUSED */;

   // Or use the signal
   assign debug_out = unused_sig;

**Width mismatches:**

.. code-block:: systemverilog

   // Bad - implicit truncation
   logic [7:0] narrow;
   logic [15:0] wide;
   assign narrow = wide;

   // Good - explicit truncation
   assign narrow = wide[7:0];

**Incomplete case:**

.. code-block:: systemverilog

   // Bad - missing default
   always_comb begin
       case (sel)
           2'b00: out = a;
           2'b01: out = b;
       endcase
   end

   // Good - with default
   always_comb begin
       case (sel)
           2'b00: out = a;
           2'b01: out = b;
           default: out = '0;
       endcase
   end


Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Linter not found:**

Ensure verilator or slang is installed and in your PATH:

.. code-block:: bash

   # Check if verilator is available
   verilator --version

   # Install verilator (Ubuntu)
   sudo apt-get install verilator

**Syntax errors:**

Check if the code compiles with the simulator first:

.. code-block:: bash

   aly sim --top tb_design

**False positives:**

Use inline comments to suppress specific warnings in code.


Next Steps
----------

- :doc:`simulation` - Run simulations
- :doc:`synthesis` - Synthesize designs
- :doc:`configuration` - Full configuration reference
