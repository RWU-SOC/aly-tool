Extension Development
=====================

ALY supports custom extension commands, similar to Zephyr's West tool.

Quick Start
-----------

1. Create ``.aly/commands.yml`` in your project:

.. code-block:: yaml

   aly-commands:
     - file: scripts/my_commands.py
       commands:
         - name: simulate
           class: Simulate
           help: run RTL simulation

2. Create ``scripts/my_commands.py``:

.. code-block:: python

   from aly.commands import AlyCommand

   class Simulate(AlyCommand):
       @staticmethod
       def add_parser(parser_adder):
           parser = parser_adder.add_parser(
               'simulate',
               help='run RTL simulation'
           )
           parser.add_argument('testbench', help='testbench to run')
           return parser
       
       def run(self, args, unknown_args):
           self.inf(f"Running {args.testbench}")
           # Your simulation logic here
           return 0

3. Use it:

.. code-block:: bash

   aly simulate my_testbench

Command YAML Schema
-------------------

The ``.aly/commands.yml`` file follows this schema:

.. code-block:: yaml

   aly-commands:
     - file: <path-to-python-file>
       commands:
         - name: <command-name>
           class: <class-name>
           help: <help-text>

* ``file`` - Path to Python file (relative to YAML location)
* ``name`` - Command name (what user types)
* ``class`` - Python class name
* ``help`` - Short help text

AlyCommand Base Class
---------------------

All commands inherit from ``AlyCommand``:

.. code-block:: python

   from aly.commands import AlyCommand

   class MyCommand(AlyCommand):
       @staticmethod
       def add_parser(parser_adder):
           """Add command's argparse subparser."""
           parser = parser_adder.add_parser('mycmd', help='my command')
           parser.add_argument('arg1', help='first argument')
           return parser
       
       def run(self, args, unknown_args):
           """Run the command."""
           self.inf(f"Running with {args.arg1}")
           return 0  # 0 = success

Available Methods
~~~~~~~~~~~~~~~~~

Commands have these logging methods:

.. code-block:: python

   self.dbg("Debug message")     # Verbose mode only
   self.inf("Info message")      # Normal output
   self.wrn("Warning message")   # Warnings
   self.err("Error message")     # Errors
   self.die("Fatal error")       # Error and exit

Properties:

* ``self.topdir`` - Project root path
* ``self.name`` - Command name
* ``self.config`` - Configuration object

Example: RTL Simulation
-----------------------

Complete example for RTL simulation:

.. code-block:: yaml

   # .aly/commands.yml
   aly-commands:
     - file: scripts/rtl_commands.py
       commands:
         - name: simulate
           class: Simulate
           help: run Vivado simulation
         - name: waveform
           class: Waveform
           help: open waveform viewer

.. code-block:: python

   # scripts/rtl_commands.py
   from pathlib import Path
   import subprocess
   from aly.commands import AlyCommand
   from aly.util import find_tool, run_command

   class Simulate(AlyCommand):
       @staticmethod
       def add_parser(parser_adder):
           parser = parser_adder.add_parser(
               'simulate',
               help='run Vivado simulation'
           )
           parser.add_argument('testbench', help='testbench file')
           parser.add_argument('--gui', action='store_true',
                             help='open GUI')
           return parser
       
       def run(self, args, unknown_args):
           # Check Vivado
           if not find_tool('xvlog.bat'):
               self.die("Vivado not found in PATH")
           
           tb_file = Path(args.testbench)
           if not tb_file.exists():
               self.die(f"Testbench not found: {tb_file}")
           
           self.inf(f"Simulating {tb_file.name}")
           
           # Compile
           self.inf("Compiling...")
           run_command(['xvlog.bat', '--sv', str(tb_file)])
           
           # Elaborate
           self.inf("Elaborating...")
           run_command(['xelab.bat', tb_file.stem])
           
           # Simulate
           cmd = ['xsim.bat', tb_file.stem]
           if args.gui:
               cmd.append('--gui')
           
           self.inf("Running simulation...")
           run_command(cmd)
           
           self.inf("✓ Simulation complete")
           return 0

   class Waveform(AlyCommand):
       @staticmethod
       def add_parser(parser_adder):
           parser = parser_adder.add_parser(
               'waveform',
               help='open waveform viewer'
           )
           parser.add_argument('waveform', help='waveform file')
           return parser
       
       def run(self, args, unknown_args):
           waveform = Path(args.waveform)
           if not waveform.exists():
               self.die(f"Waveform not found: {waveform}")
           
           # Open in GTKWave or Vivado
           if find_tool('gtkwave'):
               subprocess.Popen(['gtkwave', str(waveform)])
           elif find_tool('xsim.bat'):
               subprocess.Popen(['xsim.bat', '--gui', str(waveform)])
           else:
               self.die("No waveform viewer found")
           
           return 0

Extension Discovery
-------------------

ALY looks for extensions in:

1. ``.aly/commands.yml`` in project root
2. Paths in ``aly.commands-path`` config setting

Set custom paths:

.. code-block:: bash

   # Add to project config
   aly config set aly.commands-path /path/to/commands.yml

   # Or use environment variable
   export ALY_ALY_COMMANDS_PATH=/path/to/commands.yml

Best Practices
--------------

1. **Keep commands simple** - One clear purpose per command
2. **Validate early** - Check prerequisites before doing work
3. **Use logging methods** - Don't use ``print()`` directly
4. **Return proper codes** - 0 for success, non-zero for errors
5. **Document arguments** - Add good help text
6. **Handle errors** - Catch exceptions and show useful messages

Testing Extensions
------------------

Test your extensions:

.. code-block:: python

   # test_extensions.py
   import pytest
   from scripts.my_commands import MyCommand

   def test_my_command():
       cmd = MyCommand()
       args = type('Args', (), {'arg1': 'test'})()
       result = cmd.run(args, [])
       assert result == 0

Run with pytest:

.. code-block:: bash

   pip install pytest
   pytest test_extensions.py

Distributing Extensions
-----------------------

Share extensions by:

1. **Git repository** - Clone into project
2. **PyPI package** - Install with pip
3. **Project template** - Include in ``aly init`` templates

Example package structure::

   my-aly-extensions/
   ├── aly_extensions/
   │   └── commands.py
   ├── commands.yml
   ├── pyproject.toml
   └── README.md

See Also
--------

* :doc:`api` - API documentation for ``AlyCommand``
* :doc:`commands` - Built-in command reference
* `West Extensions <https://docs.zephyrproject.org/latest/develop/west/extensions.html>`_
