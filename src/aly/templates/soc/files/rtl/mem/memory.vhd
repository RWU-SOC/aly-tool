-- Copyright 2025 ALY Project
-- SPDX-License-Identifier: Apache-2.0

-------------------------------------------------------------------------------
-- Simple Memory Module with File Loading
-- 
-- A parameterized memory with:
-- - Configurable depth and width
-- - Optional initialization from .mem file
-- - Single port or dual port modes
-- - Byte enable support
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use std.textio.all;

entity memory is
    generic (
        WIDTH     : integer := 32;
        DEPTH     : integer := 256;
        MEM_FILE  : string  := "";   -- Memory initialization file
        DUAL_PORT : boolean := false -- Enable second read port
    );
    port (
        clk_i     : in  std_logic;
        rst_ni    : in  std_logic;
        
        -- Port A (read/write)
        a_en_i    : in  std_logic;
        a_we_i    : in  std_logic;
        a_addr_i  : in  std_logic_vector(integer(ceil(log2(real(DEPTH))))-1 downto 0);
        a_wdata_i : in  std_logic_vector(WIDTH-1 downto 0);
        a_be_i    : in  std_logic_vector(WIDTH/8-1 downto 0);  -- Byte enables
        a_rdata_o : out std_logic_vector(WIDTH-1 downto 0);
        
        -- Port B (read only, active when DUAL_PORT=true)
        b_en_i    : in  std_logic;
        b_addr_i  : in  std_logic_vector(integer(ceil(log2(real(DEPTH))))-1 downto 0);
        b_rdata_o : out std_logic_vector(WIDTH-1 downto 0)
    );
end entity memory;

architecture rtl of memory is
    constant ADDR_WIDTH : integer := integer(ceil(log2(real(DEPTH))));
    
    type mem_t is array (0 to DEPTH-1) of std_logic_vector(WIDTH-1 downto 0);
    
    -- Function to initialize memory from file
    impure function init_mem return mem_t is
        variable mem_v : mem_t := (others => (others => '0'));
        file mem_file : text;
        variable line_v : line;
        variable data_v : std_logic_vector(WIDTH-1 downto 0);
        variable i : integer := 0;
    begin
        if MEM_FILE /= "" then
            file_open(mem_file, MEM_FILE, read_mode);
            while not endfile(mem_file) and i < DEPTH loop
                readline(mem_file, line_v);
                hread(line_v, data_v);
                mem_v(i) := data_v;
                i := i + 1;
            end loop;
            file_close(mem_file);
        end if;
        return mem_v;
    end function;
    
    signal mem : mem_t := init_mem;
    signal a_rdata_q : std_logic_vector(WIDTH-1 downto 0);
    signal b_rdata_q : std_logic_vector(WIDTH-1 downto 0);
begin

    -- Port A logic
    process(clk_i)
        variable addr_int : integer;
    begin
        if rising_edge(clk_i) then
            if a_en_i = '1' then
                addr_int := to_integer(unsigned(a_addr_i));
                if a_we_i = '1' then
                    -- Byte-enable write
                    for i in 0 to WIDTH/8-1 loop
                        if a_be_i(i) = '1' then
                            mem(addr_int)((i+1)*8-1 downto i*8) <= a_wdata_i((i+1)*8-1 downto i*8);
                        end if;
                    end loop;
                end if;
                a_rdata_q <= mem(addr_int);
            end if;
        end if;
    end process;
    
    a_rdata_o <= a_rdata_q;
    
    -- Port B logic (read-only)
    gen_port_b: if DUAL_PORT generate
        process(clk_i)
        begin
            if rising_edge(clk_i) then
                if b_en_i = '1' then
                    b_rdata_q <= mem(to_integer(unsigned(b_addr_i)));
                end if;
            end if;
        end process;
        b_rdata_o <= b_rdata_q;
    end generate;
    
    gen_no_port_b: if not DUAL_PORT generate
        b_rdata_o <= (others => '0');
    end generate;

end architecture rtl;

-------------------------------------------------------------------------------
-- ROM Module - Read-Only Memory with File Loading
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use std.textio.all;

entity rom is
    generic (
        WIDTH    : integer := 32;
        DEPTH    : integer := 256;
        MEM_FILE : string  := ""
    );
    port (
        clk_i  : in  std_logic;
        en_i   : in  std_logic;
        addr_i : in  std_logic_vector(integer(ceil(log2(real(DEPTH))))-1 downto 0);
        data_o : out std_logic_vector(WIDTH-1 downto 0)
    );
end entity rom;

architecture rtl of rom is
    type mem_t is array (0 to DEPTH-1) of std_logic_vector(WIDTH-1 downto 0);
    
    impure function init_mem return mem_t is
        variable mem_v : mem_t := (others => (others => '0'));
        file mem_file : text;
        variable line_v : line;
        variable data_v : std_logic_vector(WIDTH-1 downto 0);
        variable i : integer := 0;
    begin
        if MEM_FILE /= "" then
            file_open(mem_file, MEM_FILE, read_mode);
            while not endfile(mem_file) and i < DEPTH loop
                readline(mem_file, line_v);
                hread(line_v, data_v);
                mem_v(i) := data_v;
                i := i + 1;
            end loop;
            file_close(mem_file);
        end if;
        return mem_v;
    end function;
    
    signal mem : mem_t := init_mem;
    signal data_q : std_logic_vector(WIDTH-1 downto 0);
begin

    process(clk_i)
    begin
        if rising_edge(clk_i) then
            if en_i = '1' then
                data_q <= mem(to_integer(unsigned(addr_i)));
            end if;
        end if;
    end process;
    
    data_o <= data_q;

end architecture rtl;
