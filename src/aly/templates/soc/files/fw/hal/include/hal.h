/* Hardware Abstraction Layer */
#ifndef HAL_H
#define HAL_H

#include <stdint.h>

/* UART functions */
void hal_uart_init(uint32_t baud);
void hal_uart_putc(char c);
char hal_uart_getc(void);
void hal_uart_puts(const char *s);

/* GPIO functions */
void hal_gpio_init(void);
void hal_gpio_set(uint32_t pin, uint32_t value);
uint32_t hal_gpio_get(uint32_t pin);

/* Timer functions */
void hal_timer_init(void);
uint64_t hal_timer_get(void);
void hal_delay_us(uint32_t us);

#endif /* HAL_H */
