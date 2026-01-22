    .section .text
    .globl _start

_start:
    # Load immediate test: store and load back
    la t0, test_data
    ld t1, 0(t0)       # load doubleword
    addi t1, t1, 1
    sd t1, 8(t0)       # store to next word

    # Verify
    ld t2, 8(t0)
    li t3, 0xDEADBEEFDEADBEEF
    addi t3, t3, 1
    bne t2, t3, fail

    # success -> write 1 to GPIO addr
    li t0, 0x10000000
    li t1, 1
    sd t1, 0(t0)
    j done

fail:
    li t0, 0x10000000
    li t1, 0
    sd t1, 0(t0)

done:
    j done

    .section .data
test_data:
    .dword 0xDEADBEEFDEADBEEF
    .dword 0x0
