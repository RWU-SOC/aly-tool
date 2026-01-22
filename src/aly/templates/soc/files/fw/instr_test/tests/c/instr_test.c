/* Simple instruction sequence to verify fetch behavior */
#include <stdint.h>

volatile uint64_t result = 0;

void main(void) {
    uint64_t a = 5;
    uint64_t b = 10;
    result = a + b; // ADD

    // Signal success by writing to memory-mapped GPIO address used in sim linker
    volatile uint64_t *gpio = (volatile uint64_t *)0x10000000;
    if (result == 15) {
        *gpio = 1;
    } else {
        *gpio = 0xFF;
    }

    while (1) { asm volatile ("wfi"); }
}
