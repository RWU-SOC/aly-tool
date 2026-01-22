# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""IP/Block management for ALY.

This module provides commands for managing IP cores and reusable blocks,
including version tracking, dependency resolution, and packaging.

Each IP can have a manifest.yaml file describing its sources, testbenches,
parameters, and dependencies. IPs can also have nested manifests for RTL,
testbench, and firmware components.

IP Structure::

        ip/<name>/
            manifest.yaml         (type: ip)
            rtl/
                manifest.yaml       (type: rtl, optional)
                <name>.sv
            tb/
                manifest.yaml       (type: testbench, optional)
                tb_<name>.sv
"""

import json
import shutil
import subprocess
import yaml
from pathlib import Path
from typing import Dict, Optional

from aly import log
from aly.commands import AlyCommand
from aly.util import find_aly_root
from aly.config import ProjectConfig, IPManifest, MANIFEST_FILENAME


# =============================================================================
# RTL and Testbench Templates
# =============================================================================

RTL_TEMPLATE = """// {name} IP Core
module {name} #(
    parameter DATA_WIDTH = 32
)(
    input  logic clk,
    input  logic rst_n,
    // Add ports here
    input  logic [DATA_WIDTH-1:0] data_in,
    output logic [DATA_WIDTH-1:0] data_out
);

    // Implementation here
    assign data_out = data_in;

endmodule
"""

TB_TEMPLATE = """`timescale 1ns/1ps

module tb_{name};

    logic clk = 0;
    logic rst_n = 0;
    logic [31:0] data_in;
    logic [31:0] data_out;

    always #5 clk = ~clk;

    {name} dut (.*);

    initial begin
        rst_n = 0;
        data_in = 0;
        #100;
        rst_n = 1;
        #100;

        // Add tests here
        data_in = 32'hDEADBEEF;
        #10;
        assert(data_out == 32'hDEADBEEF);

        $display("Test passed!");
        $finish;
    end

endmodule
"""


# =============================================================================
# IP Manager
# =============================================================================


class IPManager:
    """Manager for IP cores using IPManifest directly.

    Works with ProjectConfig for manifest discovery, with fallback to
    direct directory scanning when config is not available.
    """

    def __init__(self, project_root: Path, config: Optional[ProjectConfig] = None):
        self.project_root = project_root
        self.config = config
        self.ip_dir = project_root / "ip"
        self.ip_cache = project_root / ".aly" / "ip_cache"
        self._ips: Dict[str, IPManifest] = {}

    def init(self):
        """Initialize IP management structure."""
        self.ip_dir.mkdir(parents=True, exist_ok=True)
        self.ip_cache.mkdir(parents=True, exist_ok=True)

        # Create example IP with nested manifests
        example_ip = self.ip_dir / "example_fifo"
        if not example_ip.exists():
            self._create_example_ip(example_ip)

        log.inf(f"IP directory initialized: {self.ip_dir}")

    def _create_example_ip(self, ip_path: Path):
        """Create example FIFO IP with nested manifests."""
        ip_path.mkdir(parents=True)

        # Create IP manifest (type: ip)
        ip_manifest = {
            "name": "example_fifo",
            "type": "ip",
            "version": "1.0.0",
            "description": "Example synchronous FIFO",
            "vendor": "local",
            "parameters": {
                "DATA_WIDTH": {
                    "type": "int",
                    "default": 8,
                    "description": "Data bus width",
                },
                "DEPTH": {
                    "type": "int",
                    "default": 16,
                    "description": "FIFO depth",
                },
            },
            "interfaces": ["axi_stream"],
        }
        with open(ip_path / MANIFEST_FILENAME, "w") as f:
            yaml.dump(ip_manifest, f, default_flow_style=False, sort_keys=False)

        # Create RTL directory with manifest
        (ip_path / "rtl").mkdir()
        rtl_manifest = {
            "name": "example_fifo_rtl",
            "type": "rtl",
            "language": "systemverilog",
            "modules": [
                {
                    "name": "sync_fifo",
                    "files": ["sync_fifo.sv"],
                }
            ],
        }
        with open(ip_path / "rtl" / MANIFEST_FILENAME, "w") as f:
            yaml.dump(rtl_manifest, f, default_flow_style=False, sort_keys=False)

        (ip_path / "rtl" / "sync_fifo.sv").write_text(
            """// Synchronous FIFO
module sync_fifo #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH = 16
)(
    input  logic clk,
    input  logic rst_n,
    input  logic wr_en,
    input  logic rd_en,
    input  logic [DATA_WIDTH-1:0] din,
    output logic [DATA_WIDTH-1:0] dout,
    output logic full,
    output logic empty
);
    // FIFO implementation
    localparam ADDR_WIDTH = $clog2(DEPTH);

    logic [DATA_WIDTH-1:0] mem [DEPTH-1:0];
    logic [ADDR_WIDTH:0] wr_ptr, rd_ptr;

    assign full = (wr_ptr[ADDR_WIDTH] != rd_ptr[ADDR_WIDTH]) &&
                  (wr_ptr[ADDR_WIDTH-1:0] == rd_ptr[ADDR_WIDTH-1:0]);
    assign empty = (wr_ptr == rd_ptr);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= '0;
            rd_ptr <= '0;
        end else begin
            if (wr_en && !full) begin
                mem[wr_ptr[ADDR_WIDTH-1:0]] <= din;
                wr_ptr <= wr_ptr + 1;
            end
            if (rd_en && !empty) begin
                rd_ptr <= rd_ptr + 1;
            end
        end
    end

    assign dout = mem[rd_ptr[ADDR_WIDTH-1:0]];

endmodule
"""
        )

        # Create TB directory with manifest
        (ip_path / "tb").mkdir()
        tb_manifest = {
            "name": "example_fifo_tb",
            "type": "testbench",
            "testbenches": [
                {
                    "name": "tb_sync_fifo",
                    "top": "tb_sync_fifo",
                    "files": ["tb_sync_fifo.sv"],
                }
            ],
        }
        with open(ip_path / "tb" / MANIFEST_FILENAME, "w") as f:
            yaml.dump(tb_manifest, f, default_flow_style=False, sort_keys=False)

        (ip_path / "tb" / "tb_sync_fifo.sv").write_text(
            """`timescale 1ns/1ps

module tb_sync_fifo;
    parameter DATA_WIDTH = 8;
    parameter DEPTH = 16;

    logic clk = 0;
    logic rst_n = 0;
    logic wr_en, rd_en;
    logic [DATA_WIDTH-1:0] din, dout;
    logic full, empty;

    always #5 clk = ~clk;

    sync_fifo #(
        .DATA_WIDTH(DATA_WIDTH),
        .DEPTH(DEPTH)
    ) dut (.*);

    initial begin
        rst_n = 0;
        wr_en = 0;
        rd_en = 0;
        din = 0;
        #100;
        rst_n = 1;
        #100;

        // Write some data
        @(posedge clk);
        wr_en = 1;
        din = 8'hAA;
        @(posedge clk);
        din = 8'hBB;
        @(posedge clk);
        wr_en = 0;

        // Read back
        @(posedge clk);
        rd_en = 1;
        @(posedge clk);
        assert(dout == 8'hAA) else $error("Expected AA, got %h", dout);
        @(posedge clk);
        assert(dout == 8'hBB) else $error("Expected BB, got %h", dout);
        rd_en = 0;

        $display("Test passed!");
        $finish;
    end

endmodule
"""
        )

    def load(self) -> bool:
        """Load IP configuration and discover local IPs."""
        self._ips.clear()

        # Try using ProjectConfig first
        if self.config:
            try:
                ip_dict = self.config.get_all("ip")
                for name, ip in ip_dict.items():
                    self._ips[name] = ip
                return len(self._ips) > 0
            except Exception:
                pass  # Fall back to directory scan

        # Fallback: scan ip/ directory
        if self.ip_dir.exists():
            for ip_path in self.ip_dir.iterdir():
                if ip_path.is_dir() and not ip_path.name.startswith("."):
                    manifest_path = ip_path / MANIFEST_FILENAME
                    if not manifest_path.exists():
                        manifest_path = ip_path / "ip.yaml"  # Legacy fallback

                    if manifest_path.exists():
                        try:
                            ip = IPManifest.load(manifest_path)
                            self._ips[ip.name] = ip
                        except Exception as e:
                            log.wrn(f"Failed to load IP {ip_path.name}: {e}")

        return len(self._ips) > 0

    def get_ip(self, name: str) -> Optional[IPManifest]:
        """Get an IP by name."""
        # Try config first
        if self.config:
            ip = self.config.get_ip(name)
            if ip:
                return ip

        # Fallback to loaded IPs
        return self._ips.get(name)

    def get_all_ips(self) -> Dict[str, IPManifest]:
        """Get all available IPs."""
        return self._ips

    def add_from_git(
        self, url: str, name: Optional[str] = None, version: str = "main"
    ) -> bool:
        """Add IP from git repository."""
        if not name:
            name = url.split("/")[-1].replace(".git", "")

        target_dir = self.ip_dir / name

        if target_dir.exists():
            log.wrn(f"IP {name} already exists")
            return False

        log.inf(f"Cloning {url}...")
        try:
            result = subprocess.run(
                [
                    "git",
                    "clone",
                    "--branch",
                    version,
                    "--depth",
                    "1",
                    url,
                    str(target_dir),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                log.err(f"Git clone failed: {result.stderr}")
                return False

            # Verify IP manifest exists
            if not (target_dir / MANIFEST_FILENAME).exists():
                log.wrn(
                    "No manifest.yaml found in repository, creating minimal manifest"
                )
                rtl_files = [
                    str(f.relative_to(target_dir)) for f in target_dir.rglob("*.sv")
                ]
                manifest = {
                    "name": name,
                    "type": "ip",
                    "version": version,
                    "description": f"IP from {url}",
                    "files": rtl_files,
                }
                with open(target_dir / MANIFEST_FILENAME, "w") as f:
                    yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

            log.success(f"Added IP: {name}")
            return True

        except Exception as e:
            log.err(f"Failed to add IP: {e}")
            if target_dir.exists():
                shutil.rmtree(target_dir)
            return False

    def remove(self, name: str) -> bool:
        """Remove an IP from the project."""
        ip_path = self.ip_dir / name
        if not ip_path.exists():
            log.err(f"IP not found: {name}")
            return False

        shutil.rmtree(ip_path)
        log.success(f"Removed IP: {name}")
        return True

    def create_ip(self, name: str, template: str = "basic") -> bool:
        """Create a new IP core with nested manifest structure."""
        ip_path = self.ip_dir / name
        if ip_path.exists():
            log.err(f"IP {name} already exists")
            return False

        ip_path.mkdir(parents=True)

        # Create IP manifest (type: ip)
        ip_manifest = {
            "name": name,
            "type": "ip",
            "version": "0.1.0",
            "description": f"{name} IP core",
            "vendor": "local",
            "parameters": {
                "DATA_WIDTH": {
                    "type": "int",
                    "default": 32,
                    "description": "Data width",
                },
            },
        }
        with open(ip_path / MANIFEST_FILENAME, "w") as f:
            yaml.dump(ip_manifest, f, default_flow_style=False, sort_keys=False)

        # Create RTL subdirectory with manifest
        (ip_path / "rtl").mkdir()
        rtl_manifest = {
            "name": f"{name}_rtl",
            "type": "rtl",
            "language": "systemverilog",
            "modules": [
                {
                    "name": name,
                    "files": [f"{name}.sv"],
                }
            ],
        }
        with open(ip_path / "rtl" / MANIFEST_FILENAME, "w") as f:
            yaml.dump(rtl_manifest, f, default_flow_style=False, sort_keys=False)

        # Create RTL source file
        (ip_path / "rtl" / f"{name}.sv").write_text(RTL_TEMPLATE.format(name=name))

        # Create TB subdirectory with manifest
        (ip_path / "tb").mkdir()
        tb_manifest = {
            "name": f"{name}_tb",
            "type": "testbench",
            "testbenches": [
                {
                    "name": f"tb_{name}",
                    "top": f"tb_{name}",
                    "files": [f"tb_{name}.sv"],
                }
            ],
        }
        with open(ip_path / "tb" / MANIFEST_FILENAME, "w") as f:
            yaml.dump(tb_manifest, f, default_flow_style=False, sort_keys=False)

        # Create TB source file
        (ip_path / "tb" / f"tb_{name}.sv").write_text(TB_TEMPLATE.format(name=name))

        # Create doc directory
        (ip_path / "doc").mkdir()

        log.success(f"Created IP: {name}")
        return True

    def package_ip(
        self, name: str, output_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """Package an IP for distribution."""
        ip = self.get_ip(name)
        if not ip or not ip.root_dir:
            log.err(f"IP not found: {name}")
            return None

        if not output_dir:
            output_dir = self.project_root / "build" / "ip_packages"
        output_dir.mkdir(parents=True, exist_ok=True)

        package_name = f"{name}-{ip.version}"
        package_path = output_dir / f"{package_name}.tar.gz"

        import tarfile

        with tarfile.open(package_path, "w:gz") as tar:
            tar.add(ip.root_dir, arcname=package_name)

        log.success(f"Packaged IP: {package_path}")
        return package_path


# =============================================================================
# IP Command
# =============================================================================


class IP(AlyCommand):
    """IP/Block management command."""

    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser("ip", help="manage IP cores and blocks")
        subparsers = parser.add_subparsers(dest="ip_cmd", help="IP commands")

        # init - initialize IP management
        subparsers.add_parser("init", help="initialize IP management")

        # list - list available IPs
        list_parser = subparsers.add_parser("list", help="list IP cores")
        list_parser.add_argument("--json", action="store_true", help="output as JSON")

        # show - show IP details
        show_parser = subparsers.add_parser("show", help="show IP details")
        show_parser.add_argument("name", help="IP name")
        show_parser.add_argument("--json", action="store_true", help="output as JSON")

        # add - add IP to project
        add_parser = subparsers.add_parser("add", help="add IP to project")
        add_parser.add_argument("source", help="IP source (git URL or local path)")
        add_parser.add_argument(
            "--name", "-n", help="IP name (auto-detected if not specified)"
        )
        add_parser.add_argument(
            "--version", "-v", default="main", help="version/branch"
        )

        # remove - remove IP from project
        rm_parser = subparsers.add_parser("remove", help="remove IP from project")
        rm_parser.add_argument("name", help="IP name")

        # create - create new IP
        create_parser = subparsers.add_parser("create", help="create new IP core")
        create_parser.add_argument("name", help="IP name")
        create_parser.add_argument(
            "--template",
            "-t",
            default="basic",
            choices=["basic", "axi", "wishbone"],
            help="IP template",
        )

        # package - package IP for distribution
        pkg_parser = subparsers.add_parser(
            "package", help="package IP for distribution"
        )
        pkg_parser.add_argument("name", help="IP name")
        pkg_parser.add_argument("--output", "-o", help="output directory")

        # update - update IPs
        update_parser = subparsers.add_parser(
            "update", help="update IPs to latest versions"
        )
        update_parser.add_argument(
            "name", nargs="?", help="IP name (all if not specified)"
        )

        return parser

    def run(self, args, unknown_args):
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")

        # Load project config if available
        config = None
        try:
            config = ProjectConfig.load(project_root)
        except Exception:
            pass  # Config not required for all commands

        manager = IPManager(project_root, config)

        if args.ip_cmd == "init":
            return self._cmd_init(manager)
        elif args.ip_cmd == "list":
            return self._cmd_list(manager, args)
        elif args.ip_cmd == "show":
            return self._cmd_show(manager, args)
        elif args.ip_cmd == "add":
            return self._cmd_add(manager, args)
        elif args.ip_cmd == "remove":
            return self._cmd_remove(manager, args)
        elif args.ip_cmd == "create":
            return self._cmd_create(manager, args)
        elif args.ip_cmd == "package":
            return self._cmd_package(manager, args)
        elif args.ip_cmd == "update":
            return self._cmd_update(manager, args)
        else:
            return self._cmd_summary(manager)

    def _cmd_init(self, manager: IPManager) -> int:
        """Initialize IP management."""
        log.banner("Initializing IP Management")
        manager.init()
        log.success("IP management initialized")
        return 0

    def _cmd_summary(self, manager: IPManager) -> int:
        """Show IP summary."""
        manager.load()
        ips = manager.get_all_ips()

        log.banner("IP Summary")
        if not ips:
            log.inf("No IPs found. Run 'aly ip init' to set up IP management.")
            return 0

        print(f"Total IPs: {len(ips)}")
        for name, ip in ips.items():
            internal = " [nested]" if ip.has_internal_manifests() else ""
            print(
                f"  {name} v{ip.version}: {ip.description or 'No description'}{internal}"
            )

        return 0

    def _cmd_list(self, manager: IPManager, args) -> int:
        """List IPs."""
        manager.load()
        ips = manager.get_all_ips()

        if args.json:
            data = []
            for ip in ips.values():
                entry = {
                    "name": ip.name,
                    "version": ip.version,
                    "vendor": ip.vendor,
                    "description": ip.description,
                    "files": len(ip.files),
                    "has_nested_manifests": ip.has_internal_manifests(),
                }
                data.append(entry)
            print(json.dumps(data, indent=2))
        else:
            if not ips:
                log.inf("No IPs found")
                return 0

            print(f"{'Name':<20} {'Version':<12} {'Vendor':<15} Description")
            print("-" * 70)
            for ip in ips.values():
                desc = (
                    ip.description[:30] + "..."
                    if len(ip.description) > 30
                    else ip.description
                )
                nested = " [nested]" if ip.has_internal_manifests() else ""
                print(f"{ip.name:<20} {ip.version:<12} {ip.vendor:<15} {desc}{nested}")

        return 0

    def _cmd_show(self, manager: IPManager, args) -> int:
        """Show IP details with internal manifest info."""
        manager.load()
        ip = manager.get_ip(args.name)

        if not ip:
            self.die(f"IP not found: {args.name}")

        if args.json:
            data = {
                "name": ip.name,
                "version": ip.version,
                "vendor": ip.vendor,
                "description": ip.description,
                "path": str(ip.root_dir) if ip.root_dir else None,
                "files": ip.files,
                "parameters": ip.parameters,
                "interfaces": ip.interfaces,
                "has_nested_manifests": ip.has_internal_manifests(),
            }

            # Add internal manifest info
            if ip.has_internal_manifests():
                rtl = ip.get_rtl_manifest()
                if rtl:
                    data["rtl_modules"] = [m.name for m in rtl.modules]

                tb = ip.get_testbench_manifest()
                if tb:
                    data["testbenches"] = [t.name for t in tb.testbenches]

            print(json.dumps(data, indent=2))
        else:
            log.banner(f"IP: {ip.name}")
            print(f"Version: {ip.version}")
            print(f"Vendor: {ip.vendor}")
            print(f"Description: {ip.description}")
            print(f"Path: {ip.root_dir}")

            # Show direct files
            if ip.files:
                print(f"\nFiles ({len(ip.files)}):")
                for f in ip.files:
                    print(f"  {f}")

            # Show parameters
            if ip.parameters:
                print("\nParameters:")
                for name, info in ip.parameters.items():
                    if isinstance(info, dict):
                        print(
                            f"  {name}: {info.get('default', 'N/A')} - {info.get('description', '')}"
                        )
                    else:
                        print(f"  {name}: {info}")

            # Show interfaces
            if ip.interfaces:
                print(f"\nInterfaces: {', '.join(str(i) for i in ip.interfaces)}")

            # Show internal manifests
            if ip.has_internal_manifests():
                print("\nInternal Manifests:")

                rtl = ip.get_rtl_manifest()
                if rtl:
                    print(f"  RTL ({len(rtl.modules)} modules):")
                    for m in rtl.modules:
                        print(f"    - {m.name}")

                tb = ip.get_testbench_manifest()
                if tb:
                    print(f"  Testbenches ({len(tb.testbenches)} testbenches):")
                    for t in tb.testbenches:
                        print(f"    - {t.name}")

                fw = ip.get_firmware_manifest()
                if fw:
                    print(f"  Firmware: {fw.name}")

        return 0

    def _cmd_add(self, manager: IPManager, args) -> int:
        """Add IP to project."""
        log.banner("Adding IP")

        if args.source.startswith("http") or args.source.startswith("git@"):
            # Git source
            if manager.add_from_git(args.source, args.name, args.version):
                return 0
            return 1
        else:
            # Local source
            source_path = Path(args.source)
            if not source_path.exists():
                self.die(f"Source not found: {args.source}")

            name = args.name or source_path.name
            target = manager.ip_dir / name

            if target.exists():
                self.die(f"IP {name} already exists")

            shutil.copytree(source_path, target)
            log.success(f"Added IP: {name}")
            return 0

    def _cmd_remove(self, manager: IPManager, args) -> int:
        """Remove IP."""
        manager.load()
        if manager.remove(args.name):
            return 0
        return 1

    def _cmd_create(self, manager: IPManager, args) -> int:
        """Create new IP with nested manifests."""
        log.banner(f"Creating IP: {args.name}")
        if manager.create_ip(args.name, args.template):
            log.inf(f"IP created at: {manager.ip_dir / args.name}")
            log.inf("Structure:")
            log.inf(f"  {args.name}/")
            log.inf(f"    manifest.yaml     (type: ip)")
            log.inf(f"    rtl/")
            log.inf(f"      manifest.yaml   (type: rtl)")
            log.inf(f"      {args.name}.sv")
            log.inf(f"    tb/")
            log.inf(f"      manifest.yaml   (type: testbench)")
            log.inf(f"      tb_{args.name}.sv")
            return 0
        return 1

    def _cmd_package(self, manager: IPManager, args) -> int:
        """Package IP."""
        manager.load()
        output_dir = Path(args.output) if args.output else None
        if manager.package_ip(args.name, output_dir):
            return 0
        return 1

    def _cmd_update(self, manager: IPManager, args) -> int:
        """Update IPs from git."""
        log.banner("Updating IPs")
        manager.load()

        ips_to_update = [args.name] if args.name else list(manager.get_all_ips().keys())

        for name in ips_to_update:
            ip = manager.get_ip(name)
            if ip and ip.root_dir:
                git_dir = ip.root_dir / ".git"
                if git_dir.exists():
                    log.inf(f"Updating {name}...")
                    result = subprocess.run(
                        ["git", "pull"],
                        cwd=str(ip.root_dir),
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        log.success(f"  {name}: Updated")
                    else:
                        log.wrn(f"  {name}: Failed to update")
                else:
                    log.inf(f"  {name}: Skipped (not a git IP)")

        return 0
