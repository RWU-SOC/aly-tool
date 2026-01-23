============
Contributing
============

Thank you for your interest in contributing to ALY! This guide will help you get started.

.. contents::
   :local:
   :class: toc-hidden
   :depth: 2

Getting Started
---------------

Development Setup
~~~~~~~~~~~~~~~~~

1. Fork the repository on GitHub
2. Clone your fork:

   .. code-block:: bash

      git clone https://github.com/your-username/aly-tool.git
      cd aly-tool

3. Create a virtual environment:

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # or venv\Scripts\activate on Windows

4. Install in development mode:

   .. code-block:: bash

      pip install -e ".[dev]"




Project Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text

   aly-tool/
   +-- src/aly/              # Main source code
   |   +-- app/              # CLI commands
   |   +-- config/           # Configuration system
   |   +-- templates/        # Project templates
   +-- tests/                # Test suite
   +-- docs/                 # Documentation


Development Workflow
--------------------

Creating a Branch
~~~~~~~~~~~~~~~~~

Create a feature branch from ``main``:

.. code-block:: bash

   git checkout main
   git pull origin main
   git checkout -b feature/my-new-feature

Branch naming conventions:

- ``feature/`` - New features
- ``fix/`` - Bug fixes
- ``docs/`` - Documentation updates
- ``refactor/`` - Code refactoring


Making Changes
~~~~~~~~~~~~~~

1. Write your code following the style guidelines
2. Add tests for new functionality
3. Update documentation as needed
4. Run the test suite:

   .. code-block:: bash

      pytest tests/

5. Run linting:

   .. code-block:: bash

      ruff check src/
      ruff format src/


Submitting Changes
~~~~~~~~~~~~~~~~~~

1. Commit your changes:

   .. code-block:: bash

      git add .
      git commit -m "feat: add support for new simulator"

2. Push to your fork:

   .. code-block:: bash

      git push origin feature/my-new-feature

3. Open a Pull Request on GitHub


Code Style
----------

Python Style
~~~~~~~~~~~~

We follow PEP 8 with these additions:

- Line length: 88 characters (Black default)
- Use type hints for function signatures
- Use docstrings for public functions and classes

.. code-block:: python

   def load_manifest(path: Path) -> RTLManifest:
       """Load an RTL manifest from a YAML file.

       Args:
           path: Path to the manifest file.

       Returns:
           Loaded RTLManifest object.

       Raises:
           FileNotFoundError: If the manifest file doesn't exist.
           ValueError: If the manifest is invalid.
       """
       if not path.exists():
           raise FileNotFoundError(f"Manifest not found: {path}")

       with open(path) as f:
           data = yaml.safe_load(f)

       return RTLManifest.from_dict(data, path)


Commit Messages
~~~~~~~~~~~~~~~

Follow `Conventional Commits <https://www.conventionalcommits.org/>`_:

.. code-block:: text

   <type>(<scope>): <description>

   [optional body]

   [optional footer]

Types:

- ``feat``: New feature
- ``fix``: Bug fix
- ``docs``: Documentation
- ``refactor``: Code refactoring
- ``test``: Adding tests
- ``chore``: Maintenance

Examples:

.. code-block:: text

   feat(simulation): add QuestaSim backend support

   fix(synthesis): handle spaces in file paths

   docs: update installation guide


Testing
-------

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   pytest tests/

   # Run with coverage
   pytest tests/ --cov=src/aly --cov-report=html

   # Run specific test file
   pytest tests/test_config.py

   # Run specific test
   pytest tests/test_config.py::test_load_project_config


Writing Tests
~~~~~~~~~~~~~

Place tests in the ``tests/`` directory:

.. code-block:: python

   # tests/test_rtl_manifest.py
   import pytest
   from pathlib import Path
   from aly.config.models import RTLManifest


   @pytest.fixture
   def sample_manifest(tmp_path):
       manifest_file = tmp_path / "manifest.yaml"
       manifest_file.write_text("""
   name: test_design
   type: rtl
   modules:
     - name: counter
       top: counter
       files:
         - counter.sv
   """)
       return manifest_file


   def test_load_manifest(sample_manifest):
       manifest = RTLManifest.load(sample_manifest)
       assert manifest.name == "test_design"
       assert len(manifest.modules) == 1


   def test_invalid_manifest(tmp_path):
       invalid = tmp_path / "invalid.yaml"
       invalid.write_text("not: valid: yaml:")

       with pytest.raises(ValueError):
           RTLManifest.load(invalid)


Documentation
-------------

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd docs
   make html

   # View locally
   open build/html/index.html

Writing Documentation
~~~~~~~~~~~~~~~~~~~~~

- Use reStructuredText format
- Include code examples
- Add diagrams where helpful (PlantUML, Graphviz)

Example:

.. code-block:: rst

   New Feature
   -----------

   Description of the feature.

   .. code-block:: bash

      aly new-command --option value

   .. uml::

      @startuml
      Alice -> Bob: Hello
      @enduml


Adding New Features
-------------------

Adding a Simulator Backend
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create a new backend file:

   .. code-block:: python

      # src/aly/sim_newsim.py
      from pathlib import Path
      from typing import List, Dict


      class NewSimBackend:
          def __init__(self, config):
              self.config = config

          def compile(self, sources: List[Path], options: Dict) -> bool:
              # Implementation
              pass

          def elaborate(self, top: str, options: Dict) -> bool:
              # Implementation
              pass

          def simulate(self, options: Dict):
              # Implementation
              pass

2. Register the backend in ``backends.py``

3. Add configuration options in ``config/models/tools.py``

4. Update documentation

5. Add tests


Adding a CLI Command
~~~~~~~~~~~~~~~~~~~~

1. Create command module in ``app/``:

   .. code-block:: python

      # src/aly/app/mycommand.py
      import typer
      from aly.log import get_logger

      logger = get_logger(__name__)
      app = typer.Typer()


      @app.command()
      def mycommand(
          option: str = typer.Option(..., help="Description")
      ):
          """Command description."""
          logger.info(f"Running with {option}")
          # Implementation

2. Register in ``app/main.py``:

   .. code-block:: python

      from aly.app import mycommand
      app.add_typer(mycommand.app, name="mycommand")

3. Add tests and documentation


Release Process
---------------

Version Bumping
~~~~~~~~~~~~~~~

1. Update version in ``pyproject.toml``
2. Update ``CHANGELOG.md``
3. Create a release commit:

   .. code-block:: bash

      git commit -am "chore: release v1.2.0"
      git tag v1.2.0

4. Push with tags:

   .. code-block:: bash

      git push origin main --tags


Getting Help
------------

- Open an issue on GitHub for bugs or features
- Join discussions for questions
- Review existing issues before creating new ones


License
-------

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
