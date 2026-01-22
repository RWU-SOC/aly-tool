================
Template System
================

ALY uses a powerful template system to generate new projects with the ``aly init`` command. Templates are defined using YAML configuration files and Jinja2 templating, allowing for flexible project scaffolding with conditional content and variable substitution.

.. contents:: Contents
   :local:
   :depth: 3

Overview
========

Each template consists of two parts:

1. **template.yaml** - A single configuration file containing:
   - Template metadata (name, version, description)
   - Variable definitions (user-prompted or default values)
   - Directory structure to create
   - File mappings (source to destination)
   - Post-creation hooks

2. **files/** - A directory containing the actual template files, which can include:
   - Static files (copied as-is)
   - Jinja2 templates (``.j2`` extension) with variable substitution and conditionals

Template Directory Structure
============================

::

    templates/
    ├── base/                    # Base template (can be extended)
    │   ├── template.yaml
    │   └── files/
    │       ├── gitignore
    │       └── aly/
    │           └── config.yaml.j2
    │
    ├── soc/                     # SoC template (extends base)
    │   ├── template.yaml
    │   └── files/
    │       ├── rtl/
    │       │   └── top.sv.j2
    │       └── tb/
    │           └── tb_top.sv.j2
    │
    └── rv64i/                   # RV64I processor template
        ├── template.yaml
        └── files/
            ├── aly/
            ├── rtl/
            ├── tb/
            └── fw/

The template.yaml File
======================

The ``template.yaml`` file is the heart of each template. Here's a complete reference:

Basic Structure
---------------

.. code-block:: yaml

    # Template metadata
    name: my_template
    version: "1.0"
    description: "Description of what this template creates"
    extends: base  # Optional: inherit from another template

    # Variable definitions
    variables:
      project_name:
        description: "Project name"
        default: "my_project"
        pattern: "^[a-z][a-z0-9_-]*$"

      language:
        description: "HDL language"
        default: "systemverilog"
        choices:
          - systemverilog
          - verilog
          - vhdl

    # Directory structure to create
    structure:
      directories:
        - rtl
        - tb
        - docs

    # File mappings
    files:
      - src: "config.yaml.j2"
        dest: ".aly/config.yaml"
        template: true

    # Post-creation hooks
    hooks:
      post_create:
        - cmd: "git init"
          when: git_init

Variables Section
-----------------

Variables define values that users can provide or that have defaults. They are used for:

- Jinja2 template rendering (``{{ variable_name }}``)
- Conditional file creation (``when: variable_name``)
- Post-creation hook conditions

**Variable Definition Options:**

.. code-block:: yaml

    variables:
      # Full definition with all options
      project_name:
        description: "Human-readable description shown to user"
        default: "default_value"
        choices:              # Optional: limit to specific values
          - option1
          - option2
        pattern: "^regex$"    # Optional: validate with regex
        required: true        # Optional: whether value is required

      # Simple definition (just a default value)
      author: "Anonymous"

Structure Section
-----------------

Defines the directory structure to create. Supports nested directories:

.. code-block:: yaml

    structure:
      directories:
        # Simple directories
        - docs
        - scripts

        # Nested directories using dict syntax
        - rtl:
            - pkg
            - core:
                - alu
                - decoder
                - regfile
            - bus
            - mem

        - tb:
            - unit
            - integration

This creates::

    project/
    ├── docs/
    ├── scripts/
    ├── rtl/
    │   ├── pkg/
    │   ├── core/
    │   │   ├── alu/
    │   │   ├── decoder/
    │   │   └── regfile/
    │   ├── bus/
    │   └── mem/
    └── tb/
        ├── unit/
        └── integration/

Files Section
-------------

Maps source files to destination paths. Each entry specifies:

.. code-block:: yaml

    files:
      # Basic file copy (no templating)
      - src: "gitignore"
        dest: ".gitignore"

      # Template file (Jinja2 rendering)
      - src: "config.yaml.j2"
        dest: ".aly/config.yaml"
        template: true

      # Conditional file (only created if condition is true)
      - src: "fw/Makefile.j2"
        dest: "fw/Makefile"
        template: true
        when: "toolchain != 'none'"

      # Glob pattern (copy multiple files)
      - src: "rtl/*.sv"
        dest: "rtl/"

**File Specification Options:**

- ``src``: Source file path relative to ``files/`` directory
- ``dest``: Destination path relative to project root
- ``template``: If ``true``, render as Jinja2 template
- ``when``: Condition expression (file is skipped if false)
- ``from_base``: If ``true``, use file from base template (for inheritance)

Glob Patterns in Files
^^^^^^^^^^^^^^^^^^^^^^

You can use glob patterns to match multiple files:

.. code-block:: yaml

    files:
      # Match all .sv files in rtl/ (not subdirectories)
      - src: "rtl/*.sv"
        dest: "rtl/"

      # Match all .sv files recursively in rtl/ and subdirectories
      - src: "rtl/**/*.sv"
        dest: "rtl/"

      # Match ALL files recursively in a directory
      - src: "tb/unit/**/*"
        dest: "tb/unit/"

      # Match all YAML files anywhere in the template
      - src: "**/*.yaml"
        dest: "config/"

      # Single character wildcard
      - src: "test?.sv"
        dest: "tb/"

Glob wildcards:

- ``*`` - matches any number of characters in a single path segment
- ``?`` - matches exactly one character
- ``**`` - matches zero or more directories recursively

**Examples:**

- ``rtl/*.sv`` - matches ``rtl/top.sv``, ``rtl/cpu.sv`` (not ``rtl/core/alu.sv``)
- ``rtl/**/*.sv`` - matches ``rtl/top.sv``, ``rtl/core/alu.sv``, ``rtl/core/decoder/decode.sv``
- ``tb/**/*`` - matches all files in ``tb/`` and all subdirectories

Directory Copy Shorthand
^^^^^^^^^^^^^^^^^^^^^^^^

You can also copy entire directories by ending the source path with ``/``:

.. code-block:: yaml

    files:
      # Copy all files from tb/unit/ recursively
      - src: "tb/unit/"
        dest: "tb/unit/"

      # Copy all firmware files
      - src: "fw/instr_test/"
        dest: "fw/instr_test/"

This is equivalent to using ``**/*`` but more concise.

When the loader encounters a glob pattern or directory, it:

1. Expands the pattern to find all matching files
2. Preserves the relative directory structure
3. Copies/renders each matched file to the destination

Conditional File Creation (when:)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``when:`` key controls whether a file is created:

.. code-block:: yaml

    files:
      # Simple variable check
      - src: "fw/Makefile.j2"
        dest: "fw/Makefile"
        when: use_firmware

      # Expression evaluation
      - src: "riscv_config.yaml.j2"
        dest: ".aly/riscv.yaml"
        when: "toolchain == 'riscv64' or toolchain == 'riscv32'"

      # Boolean literal
      - src: "optional.txt"
        dest: "optional.txt"
        when: false  # Never created

**Important:** ``when:`` controls whether the **entire file** is created or skipped.
This is different from Jinja2 conditionals inside the file content (see below).

Hooks Section
-------------

Run commands after project creation:

.. code-block:: yaml

    hooks:
      post_create:
        # Simple command
        - "echo 'Project created!'"

        # Command with condition
        - cmd: "git init"
          when: git_init

        - cmd: "git add ."
          when: git_init

        # Command with variable substitution
        - cmd: "pip install -q sphinx"
          when: true

Commands are executed in the project directory with a 120-second timeout.

Template Inheritance
--------------------

Templates can extend a base template using the ``extends:`` key:

.. code-block:: yaml

    name: soc
    extends: base  # Inherit from 'base' template

    variables:
      # Additional variables (merged with base)
      top_module:
        description: "Top module name"
        default: "top"

    files:
      # Additional files (appended to base files)
      - src: "rtl/top.sv.j2"
        dest: "rtl/top.sv"
        template: true

When extending:

- **Variables**: Child variables are merged with base variables (child overrides)
- **Files**: Base files are processed first, then child files
- **Structure**: Child structure replaces base structure entirely
- **Hooks**: Child hooks are used (not merged)

Jinja2 Templating
=================

Files with the ``.j2`` extension are processed as Jinja2 templates when ``template: true`` is set.

Variable Substitution
---------------------

Use ``{{ variable_name }}`` to insert variable values:

.. code-block:: jinja

    # Project: {{ project_name }}
    # Version: {{ project_version }}
    # Author: {{ author }}

    module {{ project_name }}_top (
        input  logic clk_i,
        input  logic rst_i
    );
    endmodule

Conditional Content
-------------------

Use ``{% if %}`` blocks to include/exclude content based on variables:

.. code-block:: jinja

    {% if toolchain == 'riscv64' %}
    PREFIX  = riscv64-unknown-elf-
    ARCH    = rv64i
    ABI     = lp64
    {% elif toolchain == 'riscv32' %}
    PREFIX  = riscv32-unknown-elf-
    ARCH    = rv32i
    ABI     = ilp32
    {% else %}
    PREFIX  =
    ARCH    =
    ABI     =
    {% endif %}

**Important Distinction:**

- ``when:`` in ``template.yaml`` → decides if the **entire file** is created or skipped
- ``{% if %}`` inside the file → decides which **lines** appear in the rendered file

You can use both together:

.. code-block:: yaml

    # In template.yaml
    files:
      - src: "fw/Makefile.j2"
        dest: "fw/Makefile"
        template: true
        when: "toolchain != 'none'"  # Skip entire file if no toolchain

.. code-block:: jinja

    # In fw/Makefile.j2
    {% if toolchain == 'riscv64' %}
    PREFIX = riscv64-unknown-elf-
    {% elif toolchain == 'riscv32' %}
    PREFIX = riscv32-unknown-elf-
    {% endif %}

    # Rest of Makefile...

Loops
-----

Use ``{% for %}`` to generate repetitive content:

.. code-block:: jinja

    // Generated GPIO instances
    {% for i in range(num_gpios) %}
    gpio_cell gpio_{{ i }} (
        .clk_i(clk),
        .data_io(gpio_io[{{ i }}])
    );
    {% endfor %}

Filters
-------

Jinja2 filters transform values:

.. code-block:: jinja

    // Module: {{ project_name | upper }}
    // File: {{ project_name | lower }}.sv

    {% if description %}
    // {{ description | wordwrap(70) }}
    {% endif %}

Common filters: ``upper``, ``lower``, ``title``, ``default``, ``join``, ``length``

Comments
--------

Jinja2 comments are not included in output:

.. code-block:: jinja

    {# This comment won't appear in the generated file #}
    module {{ project_name }}_top;
    endmodule

Complete Example
================

Here's a complete example showing how everything works together.

template.yaml
-------------

.. code-block:: yaml

    name: example
    version: "1.0"
    description: "Example template demonstrating all features"
    extends: base

    variables:
      project_name:
        description: "Project name"
        default: "my_project"
        pattern: "^[a-z][a-z0-9_-]*$"

      language:
        description: "HDL language"
        default: "systemverilog"
        choices:
          - systemverilog
          - verilog

      toolchain:
        description: "Firmware toolchain"
        default: "none"
        choices:
          - riscv64
          - riscv32
          - none

      use_jtag:
        description: "Include JTAG interface"
        default: false

    structure:
      directories:
        - rtl:
            - core
            - bus
        - tb
        - docs

    files:
      # Configuration (always created)
      - src: "aly/config.yaml.j2"
        dest: ".aly/config.yaml"
        template: true

      # RTL files
      - src: "rtl/top.sv.j2"
        dest: "rtl/top.sv"
        template: true

      # JTAG (only if enabled)
      - src: "rtl/jtag.sv.j2"
        dest: "rtl/jtag.sv"
        template: true
        when: use_jtag

      # Firmware (only if toolchain selected)
      - src: "fw/Makefile.j2"
        dest: "fw/Makefile"
        template: true
        when: "toolchain != 'none'"

    hooks:
      post_create:
        - cmd: "git init"
          when: git_init

Template File (rtl/top.sv.j2)
-----------------------------

.. code-block:: jinja

    // {{ project_name }} Top Module
    // Generated by ALY template system
    `timescale 1ns/1ps

    {% if language == 'systemverilog' %}
    import {{ project_name }}_pkg::*;
    {% endif %}

    module {{ project_name }}_top (
        input  {% if language == 'systemverilog' %}logic{% else %}wire{% endif %} clk_i,
        input  {% if language == 'systemverilog' %}logic{% else %}wire{% endif %} rst_i,
    {% if use_jtag %}
        // JTAG interface
        input  {% if language == 'systemverilog' %}logic{% else %}wire{% endif %} tck_i,
        input  {% if language == 'systemverilog' %}logic{% else %}wire{% endif %} tms_i,
        input  {% if language == 'systemverilog' %}logic{% else %}wire{% endif %} tdi_i,
        output {% if language == 'systemverilog' %}logic{% else %}wire{% endif %} tdo_o,
    {% endif %}
        output {% if language == 'systemverilog' %}logic{% else %}wire{% endif %} [7:0] gpio_o
    );

        // Core instance
        {{ project_name }}_core core_inst (
            .clk_i(clk_i),
            .rst_i(rst_i)
        );

    {% if use_jtag %}
        // JTAG instance
        {{ project_name }}_jtag jtag_inst (
            .tck_i(tck_i),
            .tms_i(tms_i),
            .tdi_i(tdi_i),
            .tdo_o(tdo_o)
        );
    {% endif %}

    endmodule : {{ project_name }}_top

Usage
-----

Create a project with this template:

.. code-block:: bash

    # Interactive mode (prompts for variables)
    aly init example my_project

    # With variable overrides
    aly init example my_project \
        --var language=verilog \
        --var toolchain=riscv64 \
        --var use_jtag=true

Fallback Without Jinja2
=======================

If Jinja2 is not installed, the template loader falls back to simple string replacement:

- ``{{ variable }}`` patterns are replaced with values
- ``{% ... %}`` blocks are removed entirely

For full template functionality, install Jinja2:

.. code-block:: bash

    pip install jinja2

API Reference
=============

TemplateLoader Class
--------------------

.. code-block:: python

    from aly.templates.loader import TemplateLoader

    loader = TemplateLoader()

    # List available templates
    templates = loader.list_templates()
    for t in templates:
        print(f"{t.name}: {t.description}")

    # Get template variables
    variables = loader.get_variables("soc")
    for v in variables:
        print(f"{v.name}: {v.description} (default: {v.default})")

    # Create a project
    loader.create_project(
        template_name="soc",
        project_path=Path("my_project"),
        variables={
            "project_name": "my_soc",
            "language": "systemverilog",
            "author": "John Doe"
        },
        log_callback=print
    )

Available Templates
===================

ALY includes these built-in templates:

**base**
    Minimal project structure with basic configuration files.
    Usually extended by other templates.

**soc**
    Full SoC template with RTL, testbenches, firmware, and synthesis setup.
    Supports multiple HDL languages and toolchains.

**rv64i**
    Complete RV64I RISC-V processor template based on the RV64IMAC_RWU project.
    Includes CPU core, bus interfaces, memory, GPIO, JTAG, and comprehensive testbenches.

List available templates:

.. code-block:: bash

    aly init --list
