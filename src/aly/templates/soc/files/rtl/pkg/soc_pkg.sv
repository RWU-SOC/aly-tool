// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// SoC Package - Common definitions and parameters
//-----------------------------------------------------------------------------
package soc_pkg;

  // Data widths
  parameter int DATA_WIDTH = 32;
  parameter int ADDR_WIDTH = 32;
  
  // Memory sizes (configurable via workflow)
  parameter int IMEM_SIZE = 4096;  // 4KB instruction memory
  parameter int DMEM_SIZE = 4096;  // 4KB data memory
  
  // Clock and reset
  parameter int CLK_FREQ_MHZ = 100;
  
  // Peripheral base addresses
  parameter logic [31:0] UART_BASE = 32'h1000_0000;
  parameter logic [31:0] GPIO_BASE = 32'h1000_1000;
  parameter logic [31:0] TIMER_BASE = 32'h1000_2000;

endpackage : soc_pkg
