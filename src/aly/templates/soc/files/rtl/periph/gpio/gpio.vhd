-- Copyright 2025 ALY Project
-- SPDX-License-Identifier: Apache-2.0

-------------------------------------------------------------------------------
-- GPIO Module - Simple General Purpose I/O
-- 
-- Basic GPIO with configurable width and direction control.
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity gpio is
    generic (
        WIDTH : integer := 8
    );
    port (
        clk_i    : in  std_logic;
        rst_ni   : in  std_logic;
        
        -- Register interface
        addr_i   : in  std_logic_vector(31 downto 0);
        wdata_i  : in  std_logic_vector(31 downto 0);
        we_i     : in  std_logic;
        re_i     : in  std_logic;
        rdata_o  : out std_logic_vector(31 downto 0);
        
        -- GPIO pins
        gpio_i   : in  std_logic_vector(WIDTH-1 downto 0);
        gpio_o   : out std_logic_vector(WIDTH-1 downto 0);
        gpio_oe_o: out std_logic_vector(WIDTH-1 downto 0)  -- Output enable (active high)
    );
end entity gpio;

architecture rtl of gpio is
    -- Register addresses
    constant REG_DATA  : std_logic_vector(3 downto 0) := x"0";  -- Data register
    constant REG_DIR   : std_logic_vector(3 downto 0) := x"4";  -- Direction (1=output)
    constant REG_INPUT : std_logic_vector(3 downto 0) := x"8";  -- Read input pins

    signal data_q       : std_logic_vector(WIDTH-1 downto 0);
    signal dir_q        : std_logic_vector(WIDTH-1 downto 0);
    signal input_sync_q : std_logic_vector(WIDTH-1 downto 0);
begin

    -- Synchronize inputs
    process(clk_i, rst_ni)
    begin
        if rst_ni = '0' then
            input_sync_q <= (others => '0');
        elsif rising_edge(clk_i) then
            input_sync_q <= gpio_i;
        end if;
    end process;

    -- Register writes
    process(clk_i, rst_ni)
    begin
        if rst_ni = '0' then
            data_q <= (others => '0');
            dir_q  <= (others => '0');
        elsif rising_edge(clk_i) then
            if we_i = '1' then
                case addr_i(3 downto 0) is
                    when REG_DATA => data_q <= wdata_i(WIDTH-1 downto 0);
                    when REG_DIR  => dir_q  <= wdata_i(WIDTH-1 downto 0);
                    when others   => null;
                end case;
            end if;
        end if;
    end process;

    -- Register reads
    process(re_i, addr_i, data_q, dir_q, input_sync_q)
        variable rdata_v : std_logic_vector(31 downto 0);
    begin
        rdata_v := (others => '0');
        if re_i = '1' then
            case addr_i(3 downto 0) is
                when REG_DATA  => rdata_v(WIDTH-1 downto 0) := data_q;
                when REG_DIR   => rdata_v(WIDTH-1 downto 0) := dir_q;
                when REG_INPUT => rdata_v(WIDTH-1 downto 0) := input_sync_q;
                when others    => rdata_v := (others => '0');
            end case;
        end if;
        rdata_o <= rdata_v;
    end process;

    -- Output assignments
    gpio_o    <= data_q;
    gpio_oe_o <= dir_q;

end architecture rtl;
