Contributing to ALY
===================

Thank you for your interest in contributing to ALY!

Code of Conduct
---------------

Be respectful and constructive in all interactions.

How to Contribute
-----------------

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a branch** for your feature: ``git checkout -b feature/my-feature``
4. **Make your changes** and add tests
5. **Run tests**: ``pytest``
6. **Commit your changes**: ``git commit -m "Add my feature"``
7. **Push to your fork**: ``git push origin feature/my-feature``
8. **Open a Pull Request** on GitHub

Development Setup
-----------------

Clone and install in development mode:

.. code-block:: bash

   git clone https://github.com/yourusername/aly.git
   cd aly
   pip install -e ".[dev]"

Code Style
----------

* Follow PEP 8
* Use type hints for function signatures
* Write docstrings for public APIs
* Keep functions small and focused
* Prefer clarity over cleverness

Running Tests
-------------

ALY uses pytest for testing. Test artifacts and coverage reports are generated in the ``build/test_results/`` directory to keep the project root clean.

Run all tests:

.. code-block:: bash

   pytest

Run with verbose output:

.. code-block:: bash

   pytest -v

Run specific test file:

.. code-block:: bash

   pytest tests/test_commands.py

Run specific test function:

.. code-block:: bash

   pytest tests/test_commands.py::test_info_command

Run tests in parallel (requires pytest-xdist):

.. code-block:: bash

   pip install pytest-xdist
   pytest -n auto

View HTML coverage report:

.. code-block:: bash

   # Coverage is automatically generated in build/test_results/htmlcov/
   # Open in browser (Linux/macOS)
   open build/test_results/htmlcov/index.html
   
   # Or serve with Python HTTP server
   python -m http.server --directory build/test_results/htmlcov 8000
   # Then visit http://localhost:8000

Test Configuration
~~~~~~~~~~~~~~~~~~

Test configuration is in ``pyproject.toml``:

* **Test directory**: ``tests/``
* **Coverage reports**: ``build/test_results/htmlcov/``
* **Pytest cache**: ``build/test_results/.pytest_cache/``
* **Coverage data**: ``build/test_results/.coverage``

The ``build/`` directory is in ``.gitignore`` and can be safely deleted.

Documentation
-------------

Update documentation in ``docs/`` for:

* New features
* API changes  
* New commands

Build HTML documentation:

.. code-block:: bash

   cd docs
   make html

View documentation:

.. code-block:: bash

   # Linux/macOS
   open build/html/index.html
   
   # Windows
   start build\html\index.html

Pull Request Guidelines
-----------------------

* Include tests for new features
* Update documentation for user-facing changes
* Follow existing code style and patterns
* Write clear, descriptive commit messages
* Keep changes focused on a single concern
* Ensure all tests pass before submitting

Questions?

ALY is licensed under Apache License 2.0.
-------

ALY is licensed under Apache License 2.0.

All contributions must be compatible with this license.
