# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""Init command - creates new ALY projects from templates."""

import argparse
from pathlib import Path

from aly import log
from aly.commands import AlyCommand
from aly.templates import TemplateLoader


class Init(AlyCommand):
    """Initialize a new ALY project from a template."""

    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            "init",
            help="initialize a new ALY project",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="Initialize a new ALY project from a template.",
            epilog="""
Examples:
  aly init my-rv64i                    # Create RV64I SoC project in ./my-rv64i
  aly init . --template rtl-only       # Initialize current dir as RTL project
  aly init my-fw -t firmware-only      # Create firmware project
  aly init --list-templates            # Show available templates

  # Pass template variables directly:
  aly init my_cpu --var language=verilog --var toolchain=riscv32
  aly init my_soc --var use_jtag=true --var num_gpios=16

  # Use custom templates directory:
  aly init my_project --template-dir /path/to/my/templates --template my_custom
""",
        )
        parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="project directory (default: current directory)",
        )
        parser.add_argument(
            "-t",
            "--template",
            default="rv64i",
            help="project template (default: rv64i). Use --list-templates to see available.",
        )
        parser.add_argument(
            "--toolchain",
            help="toolchain identifier used by templates (default: riscv64)",
            default="riscv64",
        )
        parser.add_argument(
            "--list-templates",
            action="store_true",
            help="list available templates and exit",
        )
        parser.add_argument(
            "--no-git",
            action="store_true",
            help="skip git repository initialization",
        )
        parser.add_argument(
            "--var",
            action="append",
            metavar="KEY=VALUE",
            dest="variables",
            default=[],
            help="set template variable (can be used multiple times)",
        )
        parser.add_argument(
            "--template-dir",
            metavar="PATH",
            dest="template_dir",
            default=None,
            help="custom templates directory (default: built-in templates)",
        )
        return parser

    def run(self, args, unknown_args):
        # Create loader with optional custom templates directory
        template_dir = Path(args.template_dir) if args.template_dir else None
        loader = TemplateLoader(templates_dir=template_dir)

        # List templates mode
        if args.list_templates:
            return self._list_templates(loader)

        # Resolve project path
        project_path = Path(args.path).resolve()

        # Interactive prompts for project metadata
        print()
        log.banner(f"Initializing ALY Project: {args.template}")
        print()

        # Prompt for project name with default
        default_name = project_path.name if project_path.name != "." else "my-project"
        project_name = self._prompt("Project name", default_name)

        # Validate project name
        if not project_name.replace("-", "").replace("_", "").isalnum():
            self.die(
                f"Invalid project name: {project_name}\n"
                "Use lowercase letters, numbers, hyphens, and underscores only."
            )

        # If path is current directory and name is different, create subdirectory
        if args.path == "." and project_name != Path.cwd().name:
            project_path = Path.cwd() / project_name

        # Check if directory exists and handle conflicts
        if project_path.exists():
            if any(project_path.iterdir()):
                if (project_path / ".aly").exists():
                    self.die(f"Directory {project_path} is already an ALY project")

                self.wrn(f"Directory {project_path} is not empty")
                response = input("Continue? [y/N] ")
                if response.lower() != "y":
                    log.inf("Cancelled")
                    return 1

        # Prompt for additional metadata
        author = self._prompt("Author name", "")
        version = self._prompt("Version", "1.0.0")

        # Prompt for HDL language
        language = self._prompt_choice(
            "HDL Language",
            ["systemverilog", "verilog", "vhdl"],
            default="systemverilog",
        )

        # Show summary
        log.inf(f"Location: {project_path}")
        log.inf(f"Language: {language}")

        # Prepare template variables
        variables = {
            "project_name": project_name,
            "project_version": version,
            "author": author,
            "language": language,
            "git_init": not args.no_git,
            "toolchain": args.toolchain,
        }

        # Parse and apply --var arguments (override defaults)
        for var_spec in args.variables:
            if "=" not in var_spec:
                self.wrn(f"Invalid variable format: {var_spec} (expected KEY=VALUE)")
                continue
            key, value = var_spec.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Convert string values to appropriate types
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.isdigit():
                value = int(value)

            variables[key] = value
            log.inf(f"Variable: {key}={value}")

        # Add template-specific defaults
        for var in loader.get_variables(args.template):
            if var.name not in variables:
                if var.default is not None:
                    variables[var.name] = var.default
                elif var.choices:
                    variables[var.name] = var.choices[0]

        # Check for any required variables still missing
        missing = [
            v.name
            for v in loader.get_variables(args.template)
            if v.required and (v.name not in variables or variables.get(v.name) in (None, ""))
        ]

        if missing:
            self.die(
                "Missing required template variables: " + ", ".join(missing)
                + "\nProvide them via the template, defaults, or by passing values to the init command."
            )

        # Create project directory
        project_path.mkdir(parents=True, exist_ok=True)

        # Generate project from template
        try:
            loader.create_project(
                args.template,
                project_path,
                variables,
                log_callback=log.inf,
            )
        except Exception as e:
            self.die(f"Failed to create project: {e}")

        # Success message
        print()
        log.success(f"Project initialized: {project_name}")
        print()
        log.inf("Next steps:")
        if project_path.resolve() != Path.cwd().resolve():
            print(
                f"  cd {project_path.name if project_path.parent == Path.cwd() else project_path}"
            )
        print("  aly info")

        return 0

    def _prompt(self, prompt: str, default: str) -> str:
        """Prompt user for input with a default value."""
        if default:
            response = input(f"{prompt} [{default}]: ").strip()
            return response if response else default
        else:
            response = input(f"{prompt}: ").strip()
            return response

    def _prompt_choice(self, prompt: str, choices: list, default: str = None) -> str:
        """Prompt user to select from choices."""
        choices_str = "/".join(choices)
        if default:
            # Highlight default in choices
            display_choices = [f"[{c}]" if c == default else c for c in choices]
            choices_str = "/".join(display_choices)

        while True:
            response = input(f"{prompt} ({choices_str}): ").strip().lower()
            if not response and default:
                return default
            if response in choices:
                return response
            print(f"  Invalid choice. Please select from: {', '.join(choices)}")

    def _list_templates(self, loader: TemplateLoader) -> int:
        """Display available templates."""
        log.banner("Available Templates")

        templates = [t for t in loader.list_templates() if t.name != "base"]
        if not templates:
            self.wrn("No templates found")
            return 1

        for tmpl in templates:
            print(f"\n  {log.Colors.BLUE}{log.Colors.BOLD}{tmpl.name}{log.Colors.RESET}")
            print(f"    {tmpl.description}")

            # Show variables
            try:
                variables = loader.get_variables(tmpl.name)
                if variables:
                    var_names = [v.name for v in variables if v.name != "project_name"]
                    if var_names:
                        print(f"    Variables: {', '.join(var_names)}")
            except Exception:
                pass

            # Show if extends another template
            if tmpl.extends:
                print(f"    Extends: {tmpl.extends}")

        print()
        return 0
