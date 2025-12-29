# Copyright 2025 ALY Project Contributors
# SPDX-License-Identifier: Apache-2.0

"""Memory file generation command."""

import argparse
import struct
import subprocess
from pathlib import Path
from typing import Optional

from aly.commands import AlyCommand
from aly import log
from aly.util import find_aly_root, find_tool


class GenMem(AlyCommand):
    """Generate memory initialization files from ELF binaries."""
    
    @staticmethod
    def add_parser(parser_adder):
        parser = parser_adder.add_parser(
            'gen-mem',
            help='generate memory files from ELF',
            description='Convert ELF binary to memory initialization format'
        )
        
        parser.add_argument(
            'elf_file',
            type=Path,
            help='input ELF file'
        )
        
        parser.add_argument(
            '-o', '--output',
            type=Path,
            help='output file (default: derived from input)'
        )
        
        parser.add_argument(
            '--format',
            choices=['hex', 'bin', 'mem', 'coe', 'verilog'],
            default='hex',
            help='output format (default: hex)'
        )
        
        parser.add_argument(
            '--word-width',
            type=int,
            choices=[8, 16, 32, 64],
            default=32,
            help='memory word width in bits (default: 32)'
        )
        
        parser.add_argument(
            '--byte-order',
            choices=['little', 'big'],
            default='little',
            help='byte order (default: little)'
        )
        
        parser.add_argument(
            '--start-addr',
            type=lambda x: int(x, 0),
            default=0,
            help='start address (default: 0x00000000)'
        )
        
        parser.add_argument(
            '--size',
            type=lambda x: int(x, 0),
            help='memory size in bytes (pads with zeros)'
        )
        
        parser.add_argument(
            '--section',
            help='extract specific section (e.g., .text, .data)'
        )
        
        return parser
    
    def run(self, args, unknown_args):
        # Find project root (optional for this command)
        project_root = find_aly_root() or Path.cwd()
        
        # Resolve input file
        elf_file = args.elf_file
        if not elf_file.is_absolute():
            elf_file = project_root / elf_file
        
        if not elf_file.exists():
            self.die(f"ELF file not found: {elf_file}")
        
        # Determine output file
        if args.output:
            output_file = args.output
        else:
            output_file = elf_file.with_suffix(f'.{args.format}')
        
        if not output_file.is_absolute():
            output_file = project_root / output_file
        
        log.banner("Memory File Generation")
        log.inf(f"Input: {elf_file}")
        log.inf(f"Output: {output_file}")
        log.inf(f"Format: {args.format}")
        log.inf(f"Word width: {args.word_width} bits")
        
        # Extract binary data
        try:
            binary_data = self._extract_binary(
                elf_file=elf_file,
                start_addr=args.start_addr,
                section=args.section
            )
        except Exception as e:
            self.die(f"Failed to extract binary: {e}")
        
        if not binary_data:
            self.die("No data extracted from ELF file")
        
        log.inf(f"Extracted {len(binary_data)} bytes")
        
        # Pad to size if specified
        if args.size:
            if len(binary_data) > args.size:
                log.wrn(f"Data size ({len(binary_data)}) exceeds specified size ({args.size}), truncating")
                binary_data = binary_data[:args.size]
            elif len(binary_data) < args.size:
                padding = args.size - len(binary_data)
                binary_data += b'\x00' * padding
                log.dbg(f"Padded with {padding} zero bytes")
        
        # Convert format
        try:
            self._write_format(
                data=binary_data,
                output_file=output_file,
                format=args.format,
                word_width=args.word_width,
                byte_order=args.byte_order
            )
        except Exception as e:
            self.die(f"Failed to write output: {e}")
        
        log.success(f"✓ Generated {output_file}")
        return 0
    
    def _extract_binary(
        self,
        elf_file: Path,
        start_addr: int,
        section: Optional[str]
    ) -> bytes:
        """
        Extract binary data from ELF using objcopy.
        
        Args:
            elf_file: Path to ELF file
            start_addr: Start address for extraction
            section: Specific section to extract
            
        Returns:
            Binary data as bytes
        """
        # Try to find objcopy in RISC-V toolchain
        objcopy_candidates = [
            'riscv64-unknown-elf-objcopy',
            'riscv64-linux-gnu-objcopy',
            'riscv32-unknown-elf-objcopy',
            'objcopy',
        ]
        
        objcopy = None
        for candidate in objcopy_candidates:
            if find_tool(candidate):
                objcopy = candidate
                break
        
        if not objcopy:
            self.die("objcopy not found. Install RISC-V toolchain.")
        
        log.dbg(f"Using {objcopy}")
        
        # Build command
        temp_bin = elf_file.with_suffix('.tmp.bin')
        cmd = [objcopy, '-O', 'binary']
        
        if section:
            cmd.extend(['--only-section', section])
        
        cmd.extend([str(elf_file), str(temp_bin)])
        
        # Run objcopy
        log.dbg(f"Command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"objcopy failed: {result.stderr}")
        
        # Read binary data
        try:
            with open(temp_bin, 'rb') as f:
                data = f.read()
        finally:
            # Clean up temp file
            if temp_bin.exists():
                temp_bin.unlink()
        
        return data
    
    def _write_format(
        self,
        data: bytes,
        output_file: Path,
        format: str,
        word_width: int,
        byte_order: str
    ):
        """
        Write data in specified format.
        
        Args:
            data: Binary data
            output_file: Output file path
            format: Output format
            word_width: Word width in bits
            byte_order: Byte order ('little' or 'big')
        """
        word_bytes = word_width // 8
        
        # Pad data to word boundary
        remainder = len(data) % word_bytes
        if remainder:
            padding = word_bytes - remainder
            data += b'\x00' * padding
        
        # Convert to words
        words = []
        for i in range(0, len(data), word_bytes):
            word_data = data[i:i+word_bytes]
            if byte_order == 'little':
                word = int.from_bytes(word_data, 'little')
            else:
                word = int.from_bytes(word_data, 'big')
            words.append(word)
        
        # Write in specified format
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'hex':
            self._write_hex(words, output_file, word_width)
        elif format == 'bin':
            self._write_bin(data, output_file)
        elif format == 'mem':
            self._write_mem(words, output_file, word_width)
        elif format == 'coe':
            self._write_coe(words, output_file, word_width)
        elif format == 'verilog':
            self._write_verilog(words, output_file, word_width)
    
    def _write_hex(self, words, output_file, word_width):
        """Intel HEX format."""
        hex_digits = word_width // 4
        with open(output_file, 'w') as f:
            for word in words:
                f.write(f"{word:0{hex_digits}x}\n")
    
    def _write_bin(self, data, output_file):
        """Raw binary format."""
        with open(output_file, 'wb') as f:
            f.write(data)
    
    def _write_mem(self, words, output_file, word_width):
        """Verilog $readmemh format."""
        hex_digits = word_width // 4
        with open(output_file, 'w') as f:
            f.write("// Memory initialization file\n")
            f.write(f"// {len(words)} words, {word_width} bits each\n")
            f.write("@0\n")
            for i, word in enumerate(words):
                f.write(f"{word:0{hex_digits}x}\n")
    
    def _write_coe(self, words, output_file, word_width):
        """Xilinx COE format."""
        hex_digits = word_width // 4
        with open(output_file, 'w') as f:
            f.write("; Memory initialization file for Xilinx\n")
            f.write(f"memory_initialization_radix=16;\n")
            f.write(f"memory_initialization_vector=\n")
            for i, word in enumerate(words):
                sep = ',' if i < len(words) - 1 else ';'
                f.write(f"{word:0{hex_digits}x}{sep}\n")
    
    def _write_verilog(self, words, output_file, word_width):
        """Verilog array initialization."""
        hex_digits = word_width // 4
        with open(output_file, 'w') as f:
            f.write("// Verilog memory array initialization\n")
            f.write(f"// {len(words)} words, {word_width} bits each\n")
            f.write(f"logic [{word_width-1}:0] mem [0:{len(words)-1}] = '{{\n")
            for i, word in enumerate(words):
                sep = ',' if i < len(words) - 1 else ''
                f.write(f"    {word_width}'h{word:0{hex_digits}x}{sep}\n")
            f.write("};\n")
