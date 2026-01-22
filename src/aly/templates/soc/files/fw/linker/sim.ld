/* Linker script for simulation */
OUTPUT_ARCH("riscv")
ENTRY(_start)

MEMORY {
    IMEM (rx)  : ORIGIN = 0x00000000, LENGTH = 64K
    DMEM (rwx) : ORIGIN = 0x10000000, LENGTH = 64K
}

_stack_size = 4K;

SECTIONS {
    .text : {
        *(.text.start)
        *(.text.trap)
        *(.text*)
    } > IMEM

    .rodata : {
        *(.rodata*)
    } > DMEM

    .data : {
        *(.data*)
    } > DMEM

    .bss : {
        _bss_start = .;
        *(.bss*)
        *(COMMON)
        _bss_end = .;
    } > DMEM

    .stack (NOLOAD) : {
        . = ALIGN(16);
        . = . + _stack_size;
        _stack_top = .;
    } > DMEM
}
