# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""RTL module management for ALY.

This module provides commands for managing RTL modules within a project,
including initialization, file tracking, and module listing.

The RTL manifest (manifest.yaml) supports multiple modules per file using the
multi-module format with a 'modules:' key.
"""

import glob as globlib
import json
from pathlib import Path
from typing import List


from aly import log
from aly.util import find_aly_root
from aly.commands import AlyCommand
from aly.config.project_config import ProjectConfig
from aly.config.models.rtl import RTLManifest, RTLModule
from aly.config.models.helpers import HDLLanguage
from aly.config.models.core import MANIFEST_FILENAME


class RTL(AlyCommand):
    """RTL module management command."""


    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            "rtl",
            help="manage RTL modules",
            description="Manage RTL design modules and their source files.",
        )

        subparsers = parser.add_subparsers(dest="rtl_cmd", help="RTL commands")

        # init - initialize RTL manifest in current directory
        init_parser = subparsers.add_parser(
            "init",
            help="initialize RTL manifest in current directory",
            description="Create a new rtl.yaml manifest with interactive prompts.",
        )
        init_parser.add_argument(
            "--name",
            "-n",
            help="module name (default: current directory name)",
        )
        init_parser.add_argument(
            "--scan",
            "-s",
            action="store_true",
            help="scan for HDL files and add them automatically",
        )

        # add - add files/patterns to a module
        add_parser = subparsers.add_parser(
            "add",
            help="add source files or patterns to a module",
            description="Add file paths or glob patterns to an RTL module's sources list.",
        )
        add_parser.add_argument(
            "sources",
            nargs="+",
            help="file paths or glob patterns to add (e.g., *.sv, rtl/**/*.v)",
        )
        add_parser.add_argument(
            "--module",
            "-m",
            help="target module name (uses first module if not specified)",
        )
        add_parser.add_argument(
            "--manifest",
            "-f",
            default=MANIFEST_FILENAME,
            help=f"manifest file (default: {MANIFEST_FILENAME})",
        )

        # list - list RTL modules
        list_parser = subparsers.add_parser(
            "list",
            help="list RTL modules defined in manifest(s)",
            description="Display all RTL modules found in the manifest.",
        )
        list_parser.add_argument(
            "--manifest",
            "-f",
            default=MANIFEST_FILENAME,
            help=f"manifest file (default: {MANIFEST_FILENAME})",
        )
        list_parser.add_argument(
            "--json",
            action="store_true",
            help="output as JSON",
        )
        list_parser.add_argument(
            "--files",
            action="store_true",
            help="also show resolved file paths",
        )

        # show - show details of a specific module
        show_parser = subparsers.add_parser(
            "show",
            help="show RTL module details",
            description="Display detailed information about a specific RTL module.",
        )
        show_parser.add_argument(
            "name",
            help="module name to show",
        )
        show_parser.add_argument(
            "--manifest",
            "-f",
            default=MANIFEST_FILENAME,
            help=f"manifest file (default: {MANIFEST_FILENAME})",
        )
        show_parser.add_argument(
            "--json",
            action="store_true",
            help="output as JSON",
        )

        # packages - list named packages
        packages_parser = subparsers.add_parser(
            "packages",
            help="list named packages defined in manifests",
            description="Display all named packages across RTL manifests.",
        )
        packages_parser.add_argument(
            "--json",
            action="store_true",
            help="output as JSON",
        )

        return parser


    def run(self, args, unknown_args):
        if args.rtl_cmd == "init":
            return self._cmd_init(args)
        elif args.rtl_cmd == "add":
            return self._cmd_add(args)
        elif args.rtl_cmd == "list":
            return self._cmd_list(args)
        elif args.rtl_cmd == "show":
            return self._cmd_show(args)
        elif args.rtl_cmd == "packages":
            return self._cmd_packages(args)
        else:
            # Default: show summary
            return self._cmd_summary(args)


    def _prompt(self, prompt: str, default: str) -> str:
        """Prompt user for input with a default value."""
        if default:
            response = input(f"{prompt} [{default}]: ").strip()
            return response if response else default
        else:
            response = input(f"{prompt}: ").strip()
            return response


    def _prompt_choice(
        self, prompt: str, choices: list, default: str = "systemverilog"
    ) -> str:
        """Prompt user to select from choices."""
        choices_str = "/".join(choices)
        if default:
            display_choices = [f"[{c}]" if c == default else c for c in choices]
            choices_str = "/".join(display_choices)

        while True:
            response = input(f"{prompt} ({choices_str}): ").strip().lower()
            if not response and default:
                return default
            if response in choices:
                return response
            print(f"  Invalid choice. Please select from: {', '.join(choices)}")


    def _scan_hdl_files(self, directory: Path, language: str) -> List[str]:
        """Scan directory for HDL files based on language.

        Args:
            directory: Directory to scan
            language: HDL language (systemverilog, verilog, vhdl)

        Returns:
            List of relative file paths
        """
        extensions = HDLLanguage.get_extensions(language)
        files = []

        for ext in extensions:
            pattern = f"**/*{ext}"
            for path in sorted(directory.glob(pattern)):
                # Get relative path
                try:
                    rel_path = path.relative_to(directory)
                    files.append(str(rel_path).replace("\\", "/"))
                except ValueError:
                    files.append(str(path))

        return files


    def _cmd_init(self, args) -> int:
        """Initialize RTL manifest in current directory."""
        cwd = Path.cwd()
        manifest_path = cwd / MANIFEST_FILENAME

        # Check if manifest already exists
        if manifest_path.exists():
            self.wrn(f"Manifest already exists: {manifest_path}")
            response = input("Overwrite? [y/N] ").strip().lower()
            if response != "y":
                log.inf("Cancelled")
                return 1

        print()
        log.banner("Initialize RTL Module")
        print()

        # Prompt for module name
        default_name = args.name or cwd.name
        module_name = self._prompt("Module name", default_name)

        # Prompt for author
        author = self._prompt("Author", "")

        # Prompt for version
        version = self._prompt("Version", "1.0.0")

        # Prompt for language
        language = self._prompt_choice(
            "HDL Language",
            HDLLanguage.ALL,
            default="systemverilog",
        )

        # Scan for files if requested
        files: List[str] = []
        if args.scan:
            log.inf("Scanning for HDL files...")
            files = self._scan_hdl_files(cwd, language)
            if files:
                log.inf(f"Found {len(files)} file(s)")
                for f in files[:10]:  # Show first 10
                    print(f"    {f}")
                if len(files) > 10:
                    print(f"    ... and {len(files) - 10} more")
            else:
                log.inf("No HDL files found")

        # Create the module
        module = RTLModule(
            name=module_name,
            author=author,
            version=version,
            language=language,
            files=files,
            dependencies=[],
        )

        # Create manifest and save
        manifest = RTLManifest(
            name=module_name,
            type="rtl",
            version=version,
            description=f"RTL module: {module_name}",
            author=author,
            modules=[module],
            _manifest_path=manifest_path,
        )
        manifest.save()

        print()
        log.success(f"Created RTL manifest: {manifest_path}")
        log.inf(f"Module '{module_name}' initialized with {len(files)} file(s)")

        if not files:
            log.inf("Use 'aly rtl add <files...>' to add source files")

        return 0

    def _cmd_add(self, args) -> int:
        """Add source files or patterns to a module."""
        cwd = Path.cwd()
        manifest_path = cwd / args.manifest

        # Load existing manifest
        if not manifest_path.exists():
            self.die(f"Manifest not found: {manifest_path}\nRun 'aly rtl init' first.")

        try:
            manifest = RTLManifest.load(manifest_path)
        except Exception as e:
            self.die(f"Failed to load manifest: {e}")

        if not manifest.modules:
            self.die("No modules defined in manifest")

        # Determine target module
        target_module_name = args.module or manifest.modules[0].name
        target_module = manifest.get_module(target_module_name)
        if not target_module:
            self.die(f"Module not found: {target_module_name}")

        # Process sources - can be paths or glob patterns
        added_count = 0
        for source in args.sources:
            # Check if it's a glob pattern (contains * or ?)
            if "*" in source or "?" in source:
                matches = list(globlib.glob(source, recursive=True))
                if not matches:
                    self.wrn(f"Pattern matches no files: {source}")
                else:
                    log.inf(f"Pattern '{source}' matches {len(matches)} file(s)")

                if source not in target_module.files:
                    target_module.files.append(source)
                    added_count += 1
            else:
                file_path = Path(source)
                if not file_path.exists():
                    self.wrn(f"File not found: {source}")
                    continue

                try:
                    rel_path = file_path.relative_to(cwd)
                    normalized = str(rel_path).replace("\\", "/")
                except ValueError:
                    normalized = str(file_path).replace("\\", "/")

                if normalized not in target_module.files:
                    target_module.files.append(normalized)
                    added_count += 1
                    log.inf(f"Added: {normalized}")
                else:
                    log.inf(f"Already tracked: {normalized}")

        # Save updated manifest
        manifest.save()

        log.success(f"Added {added_count} source(s) to module '{target_module_name}'")
        return 0


    def _cmd_list(self, args) -> int:
        """List RTL modules defined in the project (optionally show files)."""
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        try:
            config = ProjectConfig.load(project_root)
        except Exception as e:
            self.die(f"Failed to load configuration: {e}")

        modules_data = []

        for ref in config.iter_rtl_modules():
            module: RTLModule = ref.obj
            manifest: RTLManifest = ref.manifest

            entry = {
                "name": module.name,
                "author": module.author,
                "version": module.version,
                "language": module.language,
                "files_count": len(module.files),
                "manifest": manifest.name,
                "manifest_path": str(manifest._manifest_path)
                if getattr(manifest, "_manifest_path", None)
                else None,
            }

            if args.files:
                all_files = manifest.get_files_for_module(module.name)
                entry["files"] = module.files
                entry["resolved_files"] = [str(p) for p in all_files]

            modules_data.append(entry)

        if args.json:
            print(json.dumps(modules_data, indent=2))
            return 0

        if not modules_data:
            log.inf("No RTL modules found in project")
            return 0

        log.banner("RTL Modules")

        for entry in modules_data:
            print(f"\n  {log.Colors.BOLD}{entry['name']}{log.Colors.RESET}")
            print(f"    Manifest: {entry['manifest']} ({entry['manifest_path']})")
            print(f"    Author:   {entry['author'] or '(not set)'}")
            print(f"    Version:  {entry['version']}")
            print(f"    Language: {HDLLanguage.get_display_name(entry['language'])}")
            print(f"    Files:    {entry['files_count']} pattern(s)")

            if args.files and "resolved_files" in entry:
                resolved_files = entry["resolved_files"]
                print(f"    Resolved: {len(resolved_files)} file(s)")
                for f in resolved_files:
                    print(f"      - {f}")

        print()
        return 0

    def _cmd_show(self, args) -> int:
        """Show details of a specific RTL module (project-wide)."""
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        try:
            config = ProjectConfig.load(project_root)
        except Exception as e:
            self.die(f"Failed to load configuration: {e}")

        ref = config.get_rtl_module(args.name)
        if not ref:
            self.die(f"RTL module not found: {args.name}")

        module: RTLModule = ref.obj
        manifest: RTLManifest = ref.manifest
        cwd = Path.cwd()

        # Packages and files for this module
        pkg_files = manifest.get_pkg_files_for_module(module.name)
        all_files = manifest.get_files_for_module(module.name)

        if args.json:
            data = {
                "name": module.name,
                "author": module.author,
                "version": module.version,
                "language": module.language,
                "file_patterns": module.files,
                "package_files": [str(p) for p in pkg_files],
                "resolved_files": [str(p) for p in all_files],
                "dependencies": module.dependencies,
                "manifest": {
                    "name": manifest.name,
                    "path": str(manifest._manifest_path)
                    if getattr(manifest, "_manifest_path", None)
                    else None,
                    "type": manifest.type,
                    "version": manifest.version,
                },
            }
            print(json.dumps(data, indent=2))
            return 0

        log.banner(f"Module: {module.name}")

        print(
            f"Manifest: {manifest.name} "
            f"({manifest._manifest_path if getattr(manifest, '_manifest_path', None) else 'unknown path'})"
        )
        print(f"Author:   {module.author or '(not set)'}")
        print(f"Version:  {module.version}")
        print(f"Language: {HDLLanguage.get_display_name(module.language)}")

        print(f"\nFile Patterns ({len(module.files)}):")
        for f in module.files:
            print(f"  {f}")

        print(f"\nPackage Files ({len(pkg_files)}):")
        for p in pkg_files:
            try:
                rel = p.relative_to(cwd)
                print(f"  {rel}")
            except ValueError:
                print(f"  {p}")

        print(f"\nResolved Files ({len(all_files)}):")
        for f in all_files:
            try:
                rel = f.relative_to(cwd)
                print(f"  {rel}")
            except ValueError:
                print(f"  {f}")

        if module.dependencies:
            print(f"\nDependencies ({len(module.dependencies)}):")
            for dep in module.dependencies:
                req = "required" if dep.get("required", True) else "optional"
                print(f"  {dep.get('name', '?')} ({dep.get('type', '?')}, {req})")

        return 0


    def _cmd_summary(self, args) -> int:
        """Show project-wide RTL summary (default command)."""
        project_root = find_aly_root()
        if not project_root:
            log.inf("Not in an ALY project")
            log.inf("Run 'aly init' to create a project")
            return 0

        try:
            config = ProjectConfig.load(project_root)
        except Exception as e:
            self.die(f"Failed to load configuration: {e}")

        log.banner("RTL Summary")

        refs = list(config.iter_rtl_modules())
        if not refs:
            log.inf("No RTL modules defined in project")
            return 0

        print(f"Project root: {project_root}")
        print(f"RTL modules:  {len(refs)}")
        print()

        total_files = 0
        for ref in refs:
            module: RTLModule = ref.obj
            manifest: RTLManifest = ref.manifest
            files = manifest.get_files_for_module(module.name)
            total_files += len(files)
            print(
                f"  {module.name} v{module.version}: {len(files)} file(s) "
                f"(manifest: {manifest.name})"
            )

        print(f"\nTotal files: {total_files}")

        return 0

    def _cmd_packages(self, args) -> int:
        """List named packages defined in RTL manifests."""
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        try:
            config = ProjectConfig.load(project_root)
        except Exception as e:
            self.die(f"Failed to load configuration: {e}")

        packages_data = []
        for ref in config.iter_packages():
            pkg = ref.obj
            manifest = ref.manifest

            pkg_path = manifest.resolve_path(pkg.path)
            entry = {
                "name": pkg.name,
                "path": str(pkg_path),
                "manifest": manifest.name,
                "modules": pkg.modules if pkg.modules else ["(global)"],
            }
            packages_data.append(entry)

        if args.json:
            print(json.dumps(packages_data, indent=2))
            return 0

        if not packages_data:
            log.inf("No named packages found in project")
            return 0

        log.banner("Named Packages")
        for entry in packages_data:
            print(f"\n  {log.Colors.BOLD}{entry['name']}{log.Colors.RESET}")
            print(f"    Path:     {entry['path']}")
            print(f"    Manifest: {entry['manifest']}")
            print(f"    Scope:    {', '.join(entry['modules'])}")

        print()
        return 0

