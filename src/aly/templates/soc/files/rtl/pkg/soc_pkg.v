// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// SoC Parameters - Common definitions and parameters
// 
// Note: Verilog doesn't have packages. Include this file and use `defines
// or parameters instead.
//-----------------------------------------------------------------------------

// Data widths
`define DATA_WIDTH 32
`define ADDR_WIDTH 32

// Memory sizes (configurable via workflow)
`define IMEM_SIZE 4096   // 4KB instruction memory
`define DMEM_SIZE 4096   // 4KB data memory

// Clock and reset
`define CLK_FREQ_MHZ 100

// Peripheral base addresses
`define UART_BASE  32'h1000_0000
`define GPIO_BASE  32'h1000_1000
`define TIMER_BASE 32'h1000_2000
