# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Template loader for ALY project generation."""

from __future__ import annotations

import glob
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml
import re

# Optional Jinja2 support - falls back to simple string replacement
try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined, Undefined

    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False


@dataclass
class TemplateVariable:
    """Definition of a template variable that can be prompted or provided."""

    name: str
    description: str = ""
    default: Any = None
    choices: list[str] = field(default_factory=list)
    pattern: str | None = None
    required: bool = True


@dataclass
class TemplateInfo:
    """Basic information about a template."""

    name: str
    description: str
    version: str = "1.0"
    extends: str | None = None


class TemplateLoader:
    """
    Loads and processes project templates from the templates directory.

    Each template consists of:
    - template.yaml: Single file containing metadata, variables, structure, and file mappings
    - files/: Directory containing actual template files (can include .j2 Jinja2 templates)

    Example usage:
        loader = TemplateLoader()
        templates = loader.list_templates()
        loader.create_project("soc", Path("my-project"), {"project_name": "my-soc"})
    """

    TEMPLATE_FILE = "template.yaml"

    def __init__(self, templates_dir: Path | None = None):
        """
        Initialize the template loader.

        Args:
            templates_dir: Custom templates directory. Defaults to the
                          templates directory within this package.
        """
        if templates_dir is None:
            self.templates_dir = Path(__file__).parent
        else:
            self.templates_dir = Path(templates_dir)

    def list_templates(self) -> list[TemplateInfo]:
        """
        List all available templates.

        Returns:
            List of TemplateInfo objects for each valid template.
        """
        templates = []
        for path in sorted(self.templates_dir.iterdir()):
            if not path.is_dir():
                continue
            template_file = path / self.TEMPLATE_FILE
            if not template_file.exists():
                continue

            with open(template_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            templates.append(
                TemplateInfo(
                    name=path.name,
                    description=data.get("description", ""),
                    version=data.get("version", "1.0"),
                    extends=data.get("extends"),
                )
            )
        return templates

    def get_template_names(self) -> list[str]:
        """Get list of template names for CLI choices."""
        return [t.name for t in self.list_templates()]

    def load_template(self, template_name: str) -> dict[str, Any]:
        """
        Load a template's configuration file.

        Args:
            template_name: Name of the template directory.

        Returns:
            Parsed template dictionary with added _path key.

        Raises:
            ValueError: If template doesn't exist.
        """
        template_dir = self.templates_dir / template_name
        template_file = template_dir / self.TEMPLATE_FILE

        if not template_file.exists():
            available = ", ".join(self.get_template_names())
            raise ValueError(
                f"Template '{template_name}' not found. Available: {available}"
            )

        with open(template_file, encoding="utf-8") as f:
            template = yaml.safe_load(f)

        # Store the template path for file resolution
        template["_path"] = template_dir
        return template

    def get_variables(self, template_name: str) -> list[TemplateVariable]:
        """
        Get the variables defined by a template.

        Args:
            template_name: Name of the template.

        Returns:
            List of TemplateVariable objects.
        """
        template = self.load_template(template_name)
        variables = []

        for name, spec in template.get("variables", {}).items():
            if isinstance(spec, dict):
                variables.append(
                    TemplateVariable(
                        name=name,
                        description=spec.get("description", ""),
                        default=spec.get("default"),
                        choices=spec.get("choices", []),
                        pattern=spec.get("pattern"),
                        required=spec.get("required", True),
                    )
                )
            else:
                # Simple default value
                variables.append(
                    TemplateVariable(name=name, default=spec, required=False)
                )

        return variables

    def create_project(
        self,
        template_name: str,
        project_path: Path,
        variables: dict[str, Any],
        log_callback: Callable[[str], None] | None = None,
    ) -> None:
        """
        Create a new project from a template.

        Args:
            template_name: Name of the template to use.
            project_path: Destination directory for the project.
            variables: Variable values for template rendering.
            log_callback: Optional function to call with log messages.
        """
        log = log_callback or (lambda msg: None)

        template = self.load_template(template_name)
        template_dir = template["_path"]
        files_dir = template_dir / "files"

        # Handle template inheritance
        if template.get("extends"):
            base_template = self.load_template(template["extends"])
            template = self._merge_templates(base_template, template)
            base_files_dir = base_template["_path"] / "files"
        else:
            base_files_dir = None

        # Create directory structure
        if "structure" in template:
            directories = template["structure"].get("directories", [])
            self._create_directories(project_path, directories, log)

        # Setup Jinja2 environment if available and needed
        jinja_env = self._create_jinja_env(files_dir, base_files_dir)

        # Process files
        for file_spec in template.get("files", []):
            # Determine source directory (base or current)
            if file_spec.get("from_base") and base_files_dir:
                src_dir = base_files_dir
            else:
                src_dir = files_dir

            self._process_file(
                file_spec, src_dir, project_path, variables, jinja_env, log
            )

        # Run post-create hooks
        hooks = template.get("hooks", {}).get("post_create", [])
        self._run_hooks(hooks, project_path, variables, log)

    def _create_jinja_env(
        self, files_dir: Path, base_files_dir: Path | None = None
    ) -> Environment | None:
        """Create Jinja2 environment with template directories."""
        if not HAS_JINJA2:
            return None

        # Build search path for templates
        search_paths = [str(files_dir)]
        if base_files_dir and base_files_dir.exists():
            search_paths.append(str(base_files_dir))

        # Use a permissive Undefined so templates with filters/defaults
        # continue to render even if optional variables are missing.
        return Environment(
            loader=FileSystemLoader(search_paths),
            undefined=Undefined,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _create_directories(
        self,
        base_path: Path,
        structure: list[Any],
        log: Callable[[str], None],
        prefix: str = "",
    ) -> None:
        """
        Recursively create directory structure.

        Args:
            base_path: Base directory to create structure in.
            structure: List of directory definitions (strings or nested dicts).
            log: Logging callback function.
            prefix: Current path prefix for logging.
        """
        for item in structure:
            if isinstance(item, str):
                # Simple directory name
                dir_path = base_path / item
                dir_path.mkdir(parents=True, exist_ok=True)
                log(f"  Created: {prefix}{item}/")

            elif isinstance(item, dict):
                # Nested structure: {"dirname": [children]}
                for dir_name, children in item.items():
                    dir_path = base_path / dir_name
                    dir_path.mkdir(parents=True, exist_ok=True)
                    log(f"  Created: {prefix}{dir_name}/")

                    if children:
                        self._create_directories(
                            dir_path, children, log, prefix=f"{prefix}{dir_name}/"
                        )

    def _process_file(
        self,
        spec: dict[str, Any],
        src_dir: Path,
        dest_dir: Path,
        variables: dict[str, Any],
        jinja_env: Environment | None,
        log: Callable[[str], None],
    ) -> None:
        """
        Process a single file specification.

        Args:
            spec: File specification dict with src, dest, template, when keys.
            src_dir: Source directory containing template files.
            dest_dir: Destination directory for output.
            variables: Template variables.
            jinja_env: Jinja2 environment or None.
            log: Logging callback.
        """
        src_pattern = spec["src"]
        dest_pattern = spec["dest"]
        is_template = spec.get("template", False)
        condition = spec.get("when")

        # Evaluate condition if present
        if condition and not self._evaluate_condition(condition, variables, jinja_env):
            return

        # Handle glob patterns (* or ? or **) and directory copies
        if "*" in src_pattern or "?" in src_pattern:
            # Expand glob pattern
            pattern_path = src_dir / src_pattern

            # Determine the base directory for relative path calculation
            # For patterns like "tb/unit/**/*", base is "tb/unit"
            # For patterns like "tb/unit/*", base is "tb/unit"
            # For patterns like "**/*.yaml", base is "."
            pattern_parts = src_pattern.replace("\\", "/").split("/")
            base_parts = []
            for part in pattern_parts:
                if "*" in part or "?" in part:
                    break
                base_parts.append(part)
            base_dir = "/".join(base_parts) if base_parts else "."

            # Use glob with recursive=True for ** patterns
            matched_files = glob.glob(str(pattern_path), recursive=True)

            for src_file in matched_files:
                src_path = Path(src_file)

                # Skip directories - only process files
                if src_path.is_dir():
                    continue

                # Calculate relative path from base directory
                try:
                    if base_dir == ".":
                        rel_path = src_path.relative_to(src_dir)
                    else:
                        rel_path = src_path.relative_to(src_dir / base_dir)
                except ValueError:
                    rel_path = Path(src_path.name)

                # Build destination path preserving directory structure
                dest_path = dest_dir / dest_pattern / rel_path
                self._copy_or_render(
                    src_path, dest_path, is_template, variables, jinja_env, log
                )

        # Handle directory copy (src ends with /)
        elif src_pattern.endswith("/"):
            src_path = src_dir / src_pattern.rstrip("/")
            if not src_path.exists() or not src_path.is_dir():
                return  # Skip missing directories

            # Copy all files recursively from the directory
            for src_file in src_path.rglob("*"):
                if src_file.is_dir():
                    continue
                rel_path = src_file.relative_to(src_path)
                dest_path = dest_dir / dest_pattern / rel_path
                self._copy_or_render(
                    src_file, dest_path, is_template, variables, jinja_env, log
                )
        else:
            # Single file
            src_path = src_dir / src_pattern
            if not src_path.exists():
                return  # Skip missing optional files

            # Handle .j2 extension removal
            dest_name = dest_pattern
            if dest_name.endswith(".j2"):
                dest_name = dest_name[:-3]

            dest_path = dest_dir / dest_name
            self._copy_or_render(
                src_path, dest_path, is_template, variables, jinja_env, log
            )

    def _evaluate_condition(
        self,
        condition: str,
        variables: dict[str, Any],
        jinja_env: Environment | None,
    ) -> bool:
        """Evaluate a condition expression."""
        if jinja_env:
            try:
                result = jinja_env.from_string("{{ " + condition + " }}").render(
                    **variables
                )
                return result.lower() not in ("false", "0", "", "none")
            except Exception:
                return True
        else:
            # Simple variable check without Jinja2
            return bool(variables.get(condition, True))

    def _copy_or_render(
        self,
        src: Path,
        dest: Path,
        is_template: bool,
        variables: dict[str, Any],
        jinja_env: Environment | None,
        log: Callable[[str], None],
    ) -> None:
        """
        Copy a file or render it as a template.

        Args:
            src: Source file path.
            dest: Destination file path.
            is_template: Whether to process as Jinja2 template.
            variables: Template variables.
            jinja_env: Jinja2 environment or None.
            log: Logging callback.
        """
        dest.parent.mkdir(parents=True, exist_ok=True)

        if is_template and src.suffix == ".j2":
            if jinja_env:
                # Render with Jinja2 using from_string to avoid loader path issues
                try:
                    raw = src.read_text(encoding="utf-8")
                    template = jinja_env.from_string(raw)
                    content = template.render(**variables)
                    dest.write_text(content, encoding="utf-8")
                except Exception:
                    # Fallback to simple copy if template fails
                    content = src.read_text(encoding="utf-8")
                    content = self._simple_render(content, variables)
                    dest.write_text(content, encoding="utf-8")
            else:
                # Simple string replacement fallback
                content = src.read_text(encoding="utf-8")
                content = self._simple_render(content, variables)
                dest.write_text(content, encoding="utf-8")
        else:
            # Direct copy
            shutil.copy2(src, dest)

        log(f"  Created: {dest.name}")

    def _simple_render(self, content: str, variables: dict[str, Any]) -> str:
        """
        Simple template rendering without Jinja2.

        Replaces {{ variable_name }} patterns with values.
        """
        # Remove simple Jinja2 block tags like {% if ... %}, {% endif %}, etc.
        content = re.sub(r"{%[^%]*%}", "", content)

        # Replace variable placeholders
        for key, value in variables.items():
            content = content.replace("{{ " + key + " }}", str(value))
            content = content.replace("{{" + key + "}}", str(value))
        return content

    def _merge_templates(
        self, base: dict[str, Any], child: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge a base template into a child template.

        Child values override base values. Lists are concatenated.
        """
        result = {}

        # Copy base values
        for key, value in base.items():
            if key.startswith("_"):
                continue
            result[key] = value

        # Override/extend with child values
        for key, value in child.items():
            if key == "variables":
                # Merge variables dicts
                result["variables"] = {
                    **base.get("variables", {}),
                    **child.get("variables", {}),
                }
            elif key == "files":
                # Concatenate file lists, base first
                base_files = [{**f, "from_base": True} for f in base.get("files", [])]
                result["files"] = base_files + child.get("files", [])
            elif key == "structure":
                # Child structure overrides base
                result["structure"] = value
            elif key.startswith("_"):
                continue
            else:
                result[key] = value

        # Preserve child path
        result["_path"] = child["_path"]
        return result

    def _run_hooks(
        self,
        hooks: list[dict[str, Any] | str],
        project_path: Path,
        variables: dict[str, Any],
        log: Callable[[str], None],
    ) -> None:
        """
        Run post-creation hooks.

        Args:
            hooks: List of hook definitions (strings or dicts with cmd/when).
            project_path: Working directory for commands.
            variables: Variables for condition evaluation and substitution.
            log: Logging callback.
        """
        for hook in hooks:
            if isinstance(hook, str):
                cmd = hook
                condition = None
            else:
                cmd = hook.get("cmd", "")
                condition = hook.get("when")

            # Check condition
            if condition is not None:
                # Handle boolean conditions directly
                if isinstance(condition, bool):
                    if not condition:
                        continue
                else:
                    var_name = str(condition).strip()
                    # Handle string boolean literals
                    if var_name in ("true", "True", "1"):
                        pass  # Always run
                    elif var_name in ("false", "False", "0"):
                        continue  # Never run
                    elif not variables.get(var_name, True):
                        continue

            if not cmd:
                continue

            # Substitute variables in command
            cmd = self._simple_render(cmd, variables)

            try:
                log(f"  Running: {cmd[:80]}...")
                subprocess.run(
                    cmd,
                    shell=True,
                    cwd=project_path,
                    check=False,
                    capture_output=True,
                    timeout=120,
                )
            except subprocess.TimeoutExpired:
                log(f"  Warning: Hook timed out")
            except Exception as e:
                log(f"  Warning: Hook failed: {e}")
