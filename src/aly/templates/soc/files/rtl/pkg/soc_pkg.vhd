-- Copyright 2025 ALY Project
-- SPDX-License-Identifier: Apache-2.0

-------------------------------------------------------------------------------
-- SoC Package - Common definitions and parameters
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package soc_pkg is

    -- Data widths
    constant DATA_WIDTH : integer := 32;
    constant ADDR_WIDTH : integer := 32;
    
    -- Memory sizes (configurable via workflow)
    constant IMEM_SIZE : integer := 4096;  -- 4KB instruction memory
    constant DMEM_SIZE : integer := 4096;  -- 4KB data memory
    
    -- Clock and reset
    constant CLK_FREQ_MHZ : integer := 100;
    
    -- Peripheral base addresses
    constant UART_BASE  : std_logic_vector(31 downto 0) := x"10000000";
    constant GPIO_BASE  : std_logic_vector(31 downto 0) := x"10001000";
    constant TIMER_BASE : std_logic_vector(31 downto 0) := x"10002000";

end package soc_pkg;

package body soc_pkg is
    -- Package body (empty for now)
end package body soc_pkg;
