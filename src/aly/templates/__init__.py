# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""
Template loading and project generation for ALY.

This module provides a file-based template system that replaces the previous
embedded template strings. Templates are stored as actual files with proper
syntax highlighting and are processed using optional Jinja2 templating.

Usage:
    from aly.templates import TemplateLoader

    loader = TemplateLoader()
    templates = loader.list_templates()
    loader.create_project("soc", Path("my-project"), {"project_name": "my-soc"})

Template Structure:
    templates/
    ├── base/
    │   ├── template.yaml      # Template definition (metadata, variables, files, structure)
    │   └── files/             # Actual template files
    ├── soc/
    │   ├── template.yaml
    │   └── files/
    └── ...
"""

from aly.templates.loader import TemplateInfo, TemplateLoader, TemplateVariable

__all__ = ["TemplateLoader", "TemplateInfo", "TemplateVariable"]
