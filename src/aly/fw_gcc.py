# Copyright 2025 Mohamed Aly
# SPDX-License-Identifier: Apache-2.0

"""GCC-based firmware backend for RISC-V and ARM toolchains.

This backend supports:
- RISC-V (riscv64-unknown-elf, riscv32-unknown-elf)
- ARM (arm-none-eabi)
- Custom GCC-compatible toolchains

Outputs:
- ELF executable
- Binary file
- Memory initialization file (.mem) for simulation
- Disassembly listing
"""

import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from aly import log
from aly.backends import FirmwareBackend, FirmwareResult
from aly.util import find_tool, run_command


class GccFirmwareBackend(FirmwareBackend):
    """GCC-based firmware backend.

    Supports RISC-V, ARM, and other GCC-compatible toolchains.
    """

    def __init__(self, config: Dict[str, Any], project_root: Path):
        """Initialize GCC firmware backend.

        Args:
            config: Toolchain configuration containing:
                - prefix: Toolchain prefix (e.g., 'riscv64-unknown-elf-')
                - march: Architecture (e.g., 'rv64i')
                - mabi: ABI (e.g., 'lp64')
                - cpu: CPU type (for ARM, e.g., 'cortex-m4')
            project_root: Project root directory
        """
        super().__init__(config, project_root)
        self._prefix = config.get("prefix", "")

    def check_toolchain(self) -> bool:
        """Check if the GCC toolchain is available."""
        gcc = f"{self._prefix}gcc"
        return find_tool(gcc) is not None

    def get_prefix(self) -> str:
        """Get toolchain prefix."""
        return self._prefix

    def build(
        self,
        build_config: Any,
        output_dir: Path,
        mem_formats: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> FirmwareResult:
        """Build firmware using GCC toolchain.

        Args:
            build_config: FirmwareBuildConfig instance with sources, linker, etc.
            output_dir: Output directory for build artifacts
            mem_formats: List of memory format configurations

        Returns:
            FirmwareResult with paths to generated files
        """
        start_time = time.time()
        name = build_config.name

        log.inf(f"Building: {name}")

        # Create build subdirectory
        build_dir = output_dir / name
        build_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Resolve source files
            sources = self._resolve_sources(build_config)

            if not sources:
                return FirmwareResult(
                    success=False,
                    duration=time.time() - start_time,
                    build_name=name,
                    stderr=f"No sources found for {name}",
                )

            # Separate C and ASM files
            c_files = [s for s in sources if s.suffix == ".c"]
            asm_files = [s for s in sources if s.suffix.lower() in [".s", ".asm"]]

            # Get architecture flags
            arch_flags = self._get_arch_flags()

            # Output files
            elf_file = build_dir / f"{name}.elf"
            bin_file = build_dir / f"{name}.bin"
            lst_file = build_dir / f"{name}.lst"

            # Compile C files
            c_objs = []
            for c_file in c_files:
                obj_file = build_dir / f"{c_file.stem}.o"
                if not self._compile_c(
                    c_file, obj_file, build_config, arch_flags, build_dir
                ):
                    return FirmwareResult(
                        success=False,
                        duration=time.time() - start_time,
                        build_name=name,
                        stderr=f"Failed to compile {c_file}",
                    )
                c_objs.append(obj_file)

            # Assemble ASM files
            asm_objs = []
            for asm_file in asm_files:
                obj_file = build_dir / f"{asm_file.stem}.o"
                if not self._assemble(asm_file, obj_file, arch_flags):
                    return FirmwareResult(
                        success=False,
                        duration=time.time() - start_time,
                        build_name=name,
                        stderr=f"Failed to assemble {asm_file}",
                    )
                asm_objs.append(obj_file)

            # Link
            all_objs = c_objs + asm_objs
            if not self._link(all_objs, elf_file, build_config):
                return FirmwareResult(
                    success=False,
                    duration=time.time() - start_time,
                    build_name=name,
                    stderr="Linking failed",
                )

            # Generate disassembly
            self._generate_disassembly(elf_file, lst_file)

            # Generate binary
            if not self._generate_binary(elf_file, bin_file):
                return FirmwareResult(
                    success=False,
                    duration=time.time() - start_time,
                    build_name=name,
                    elf_file=elf_file,
                    stderr="Failed to generate binary",
                )

            # Generate memory files
            mem_files = {}
            if mem_formats:
                for fmt_config in mem_formats:
                    fmt = fmt_config.get("format", "mem")
                    word_width = fmt_config.get("word_width", 32)
                    byte_order = fmt_config.get("byte_order", "little")
                    plusarg = fmt_config.get("plusarg", "MEM_FILE")

                    # Generate unique filename if multiple formats
                    if len(mem_formats) > 1:
                        suffix = f"_{word_width}" if word_width != 32 else ""
                        suffix += f"_{byte_order}" if byte_order != "little" else ""
                        mem_file = build_dir / f"{name}{suffix}.{fmt}"
                    else:
                        mem_file = build_dir / f"{name}.{fmt}"

                    if FirmwareBackend.generate_mem_file(
                        bin_file, mem_file, fmt, word_width, byte_order
                    ):
                        mem_files[plusarg] = mem_file
                        log.success(f"{name}.{fmt} ({word_width}-bit, {byte_order})")
                    else:
                        log.wrn(f"Failed to generate {mem_file.name}")
            else:
                # Default: generate .mem file
                mem_file = build_dir / f"{name}.mem"
                if FirmwareBackend.generate_mem_file(bin_file, mem_file):
                    mem_files["MEM_FILE"] = mem_file
                    log.success(f"{name}.mem")

            duration = time.time() - start_time

            return FirmwareResult(
                success=True,
                duration=duration,
                build_name=name,
                elf_file=elf_file,
                bin_file=bin_file,
                mem_files=mem_files,
                lst_file=lst_file,
            )

        except Exception as e:
            return FirmwareResult(
                success=False,
                duration=time.time() - start_time,
                build_name=name,
                stderr=str(e),
            )

    def _resolve_sources(self, build_config: Any) -> List[Path]:
        """Resolve source file paths."""
        sources = []
        for src in build_config.sources:
            # Use build config's resolve_path if available
            if hasattr(build_config, "resolve_path") and build_config._manifest_path:
                resolved = build_config.resolve_path(src)
            else:
                resolved = self.project_root / src

            # Handle glob patterns
            if "*" in str(resolved):
                parent = resolved.parent
                pattern = resolved.name
                if parent.exists():
                    sources.extend(sorted(parent.glob(pattern)))
            elif resolved.exists():
                sources.append(resolved)

        return sources

    def _get_arch_flags(self) -> List[str]:
        """Get architecture-specific compiler flags."""
        flags = []

        march = self.config.get("march")
        if march:
            flags.extend(["-march", march])

        mabi = self.config.get("mabi")
        if mabi:
            flags.extend(["-mabi", mabi])

        cpu = self.config.get("cpu")
        if cpu:
            flags.extend(["-mcpu", cpu])

        return flags

    def _compile_c(
        self,
        source: Path,
        output: Path,
        build_config: Any,
        arch_flags: List[str],
        build_dir: Path,
    ) -> bool:
        """Compile a C source file."""
        cmd = [f"{self._prefix}gcc"]
        cmd.extend(arch_flags)
        cmd.extend(["-O2", "-c", "-o", str(output), str(source)])

        # Add includes
        for inc in build_config.includes:
            if hasattr(build_config, "resolve_path") and build_config._manifest_path:
                inc_path = build_config.resolve_path(inc, self.project_root)
            else:
                inc_path = self.project_root / inc
            cmd.extend(["-I", str(inc_path)])

        # Add defines
        for key, val in build_config.defines.items():
            if val:
                cmd.extend(["-D", f"{key}={val}"])
            else:
                cmd.extend(["-D", key])

        # Add custom cflags
        if hasattr(build_config, "cflags"):
            cmd.extend(build_config.cflags)

        try:
            run_command(cmd)
            return True
        except Exception as e:
            log.err(f"Compile error: {e}")
            return False

    def _assemble(self, source: Path, output: Path, arch_flags: List[str]) -> bool:
        """Assemble an assembly source file."""
        cmd = [f"{self._prefix}as"]
        print(cmd)

        # Only pass -march to assembler (not -mabi)
        march = self.config.get("march")
        if march:
            cmd.extend(["-march", march])

        cmd.extend(["-o", str(output), str(source)])

        try:
            run_command(cmd)
            return True
        except Exception as e:
            log.err(f"Assembly error: {e}")
            return False

    def _link(self, objects: List[Path], output: Path, build_config: Any) -> bool:
        """Link object files into an ELF executable."""
        cmd = [f"{self._prefix}ld", "-o", str(output)]

        # Add linker script if specified
        if build_config.linker_script:
            if hasattr(build_config, "resolve_path") and build_config._manifest_path:
                linker = build_config.resolve_path(build_config.linker_script)
            else:
                linker = self.project_root / build_config.linker_script

            if linker.exists():
                cmd.extend(["-T", str(linker)])

        # Add object files
        cmd.extend([str(o) for o in objects])

        try:
            run_command(cmd)
            return True
        except Exception as e:
            log.err(f"Link error: {e}")
            return False

    def _generate_disassembly(self, elf_file: Path, lst_file: Path) -> bool:
        """Generate disassembly listing."""
        try:
            result = subprocess.run(
                [f"{self._prefix}objdump", "-d", "-S", str(elf_file)],
                capture_output=True,
                text=True,
                check=True,
            )
            lst_file.write_text(result.stdout)
            return True
        except Exception:
            return False

    def _generate_binary(self, elf_file: Path, bin_file: Path) -> bool:
        """Generate binary from ELF."""
        try:
            run_command(
                [
                    f"{self._prefix}objcopy",
                    "-O",
                    "binary",
                    str(elf_file),
                    str(bin_file),
                ]
            )
            return True
        except Exception:
            return False


# Aliases for specific toolchains
class RiscvFirmwareBackend(GccFirmwareBackend):
    """RISC-V GCC firmware backend."""

    pass


class ArmFirmwareBackend(GccFirmwareBackend):
    """ARM GCC firmware backend."""

    pass
