# Minimal RISC-V startup code
.section .text.start
.global _start

_start:
    # Disable interrupts
    csrci mstatus, 0x8

    # Set stack pointer
    la sp, _stack_top

    # Clear BSS section
    la t0, _bss_start
    la t1, _bss_end
1:
    bge t0, t1, 2f
    sd zero, 0(t0)
    addi t0, t0, 8
    j 1b
2:
    # Call main
    call main

    # Infinite loop if main returns
3:
    wfi
    j 3b

.section .text.trap
.global _trap_handler
_trap_handler:
    # Minimal trap handler
    mret
