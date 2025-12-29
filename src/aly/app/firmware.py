# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Firmware command - builds RISC-V firmware."""

import argparse
from pathlib import Path
import subprocess

from aly import log
from aly.commands import AlyCommand
from aly.util import find_aly_root, find_tool, run_command


class Firmware(AlyCommand):
    """Build RISC-V firmware from C/Assembly sources."""
    
    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            'firmware',
            help='build RISC-V firmware',
            description='Build firmware from C and assembly sources.'
        )
        parser.add_argument(
            'sources',
            nargs='*',
            help='source files to build (default: all in firmware/)'
        )
        parser.add_argument(
            '-o', '--output',
            help='output directory (default: .aly_build/firmware)'
        )
        return parser
    
    def run(self, args, unknown_args):
        project_root = find_aly_root()
        if not project_root:
            self.die("Not in an ALY project")
        
        # Setup paths
        firmware_dir = project_root / 'firmware'
        if not firmware_dir.exists():
            self.die(f"Firmware directory not found: {firmware_dir}")
        
        if args.output:
            output_dir = Path(args.output)
        else:
            output_dir = project_root / '.aly_build' / 'firmware'
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check toolchain
        if not self._check_toolchain():
            self.die("RISC-V toolchain not found in PATH")
        
        # Find sources
        if args.sources:
            sources = [Path(s) for s in args.sources]
        else:
            sources = list(firmware_dir.rglob('*.c')) + list(firmware_dir.rglob('*.asm'))
        
        if not sources:
            self.die(f"No firmware sources found in {firmware_dir}")
        
        log.banner(f"Building Firmware ({len(sources)} files)")
        
        # Build each source
        success_count = 0
        for src in sources:
            try:
                if src.suffix == '.asm':
                    if self._build_asm(src, output_dir, project_root):
                        success_count += 1
                elif src.suffix == '.c':
                    if self._build_c(src, output_dir, project_root):
                        success_count += 1
            except Exception as e:
                self.err(f"Failed to build {src.name}: {e}")
        
        # Summary
        print()
        log.inf(f"Built {success_count}/{len(sources)} firmware files")
        log.inf(f"Output: {output_dir}")
        
        return 0 if success_count == len(sources) else 1
    
    def _check_toolchain(self) -> bool:
        """Check if RISC-V toolchain is available."""
        tools = ['riscv64-unknown-elf-gcc', 'riscv64-unknown-elf-as',
                 'riscv64-unknown-elf-ld', 'riscv64-unknown-elf-objcopy']
        return all(find_tool(t) for t in tools)
    
    def _build_asm(self, asm_file: Path, output_dir: Path, project_root: Path) -> bool:
        """Build assembly firmware: .asm -> .elf -> .mem"""
        name = asm_file.stem
        obj_file = output_dir / f"{name}.o"
        elf_file = output_dir / f"{name}.elf"
        bin_file = output_dir / f"{name}.bin"
        mem_file = output_dir / f"{name}.mem"
        lst_file = output_dir / f"{name}.lst"
        
        self.inf(f"Building {asm_file.name}")
        
        try:
            # Assemble
            run_command([
                'riscv64-unknown-elf-as',
                '-march=rv64i',
                '-o', str(obj_file),
                str(asm_file)
            ])
            
            # Link
            run_command([
                'riscv64-unknown-elf-ld',
                '-b', 'elf64-littleriscv',
                '-o', str(elf_file),
                str(obj_file)
            ])
            
            # Disassembly
            result = subprocess.run(
                ['riscv64-unknown-elf-objdump', '-d', '-S', str(elf_file)],
                capture_output=True,
                text=True,
                check=True
            )
            lst_file.write_text(result.stdout)
            
            # Binary
            run_command([
                'riscv64-unknown-elf-objcopy',
                '-O', 'binary',
                str(elf_file),
                str(bin_file)
            ])
            
            # Hex memory file
            self._binary_to_mem(bin_file, mem_file)
            
            log.success(f"{name}.mem")
            return True
            
        except subprocess.CalledProcessError as e:
            self.err(f"Build failed: {e}")
            if e.stderr:
                self.err(e.stderr)
            return False
    
    def _build_c(self, c_file: Path, output_dir: Path, project_root: Path) -> bool:
        """Build C firmware: .c -> .elf -> .mem"""
        name = c_file.stem
        c_obj = output_dir / f"{name}.o"
        elf_file = output_dir / f"{name}.elf"
        bin_file = output_dir / f"{name}.bin"
        mem_file = output_dir / f"{name}.mem"
        
        self.inf(f"Building {c_file.name}")
        
        # Look for startup code
        firmware_dir = project_root / 'firmware'
        startup_dir = firmware_dir / 'startup'
        crt0 = startup_dir / 'crt0.s'
        linker_dir = firmware_dir / 'linker'
        linker = linker_dir / 'link.ld'
        
        try:
            # Compile C
            compile_cmd = [
                'riscv64-unknown-elf-gcc',
                '-march=rv64i',
                '-mabi=lp64',
                '-O0', '-c',
                '-o', str(c_obj),
                str(c_file)
            ]
            
            # Add include path if exists
            include_dir = firmware_dir / 'include'
            if include_dir.exists():
                compile_cmd.extend(['-I', str(include_dir)])
            
            run_command(compile_cmd)
            
            # Assemble startup if exists
            objects = [c_obj]
            if crt0.exists():
                crt0_obj = output_dir / 'crt0.o'
                run_command([
                    'riscv64-unknown-elf-as',
                    '-march=rv64i',
                    '-o', str(crt0_obj),
                    str(crt0)
                ])
                objects.insert(0, crt0_obj)
            
            # Link
            link_cmd = ['riscv64-unknown-elf-ld', '-o', str(elf_file)]
            if linker.exists():
                link_cmd.extend(['-T', str(linker)])
            link_cmd.extend([str(o) for o in objects])
            
            run_command(link_cmd)
            
            # Binary
            run_command([
                'riscv64-unknown-elf-objcopy',
                '-O', 'binary',
                str(elf_file),
                str(bin_file)
            ])
            
            # Hex memory file
            self._binary_to_mem(bin_file, mem_file)
            
            log.success(f"{name}.mem")
            return True
            
        except subprocess.CalledProcessError as e:
            self.err(f"Build failed: {e}")
            if e.stderr:
                self.err(e.stderr)
            return False
    
    def _binary_to_mem(self, bin_file: Path, mem_file: Path):
        """Convert binary to Verilog hex format (32-bit big-endian words)."""
        with open(bin_file, 'rb') as f:
            data = f.read()
        
        # Pad to 4-byte boundary
        padding = (4 - len(data) % 4) % 4
        data += b'\x00' * padding
        
        # Convert to big-endian hex words
        hex_words = []
        for i in range(0, len(data), 4):
            word = data[i:i+4]
            # Little-endian byte order in file -> big-endian hex
            hex_word = ''.join(f'{b:02x}' for b in reversed(word))
            hex_words.append(hex_word)
        
        mem_file.write_text('\n'.join(hex_words) + '\n')
