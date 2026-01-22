-- Copyright 2025 ALY Project
-- SPDX-License-Identifier: Apache-2.0

-------------------------------------------------------------------------------
-- Testbench for Memory Module (VHDL)
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity tb_memory is
end entity tb_memory;

architecture sim of tb_memory is
    -- Parameters
    constant WIDTH     : integer := 32;
    constant DEPTH     : integer := 256;
    constant CLK_PERIOD: time := 10 ns;
    constant ADDR_WIDTH: integer := integer(ceil(log2(real(DEPTH))));

    -- Signals
    signal clk     : std_logic := '0';
    signal rst_n   : std_logic := '0';
    signal a_en    : std_logic := '0';
    signal a_we    : std_logic := '0';
    signal a_addr  : std_logic_vector(ADDR_WIDTH-1 downto 0) := (others => '0');
    signal a_wdata : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
    signal a_be    : std_logic_vector(WIDTH/8-1 downto 0) := (others => '1');
    signal a_rdata : std_logic_vector(WIDTH-1 downto 0);
    signal b_en    : std_logic := '0';
    signal b_addr  : std_logic_vector(ADDR_WIDTH-1 downto 0) := (others => '0');
    signal b_rdata : std_logic_vector(WIDTH-1 downto 0);
    
    -- Test tracking
    signal test_count : integer := 0;
    signal pass_count : integer := 0;
    signal fail_count : integer := 0;
    signal sim_done   : boolean := false;

begin

    -- DUT instantiation
    dut: entity work.memory
        generic map (
            WIDTH     => WIDTH,
            DEPTH     => DEPTH,
            MEM_FILE  => "",
            DUAL_PORT => false
        )
        port map (
            clk_i     => clk,
            rst_ni    => rst_n,
            a_en_i    => a_en,
            a_we_i    => a_we,
            a_addr_i  => a_addr,
            a_wdata_i => a_wdata,
            a_be_i    => a_be,
            a_rdata_o => a_rdata,
            b_en_i    => b_en,
            b_addr_i  => b_addr,
            b_rdata_o => b_rdata
        );

    -- Clock generation
    clk_gen: process
    begin
        while not sim_done loop
            clk <= '0';
            wait for CLK_PERIOD/2;
            clk <= '1';
            wait for CLK_PERIOD/2;
        end loop;
        wait;
    end process;

    -- Test sequence
    test_proc: process
        variable expected : std_logic_vector(WIDTH-1 downto 0);
        
        procedure check(name: string; condition: boolean) is
        begin
            test_count <= test_count + 1;
            if condition then
                pass_count <= pass_count + 1;
                report "[PASS] " & name;
            else
                fail_count <= fail_count + 1;
                report "[FAIL] " & name severity warning;
            end if;
        end procedure;
        
        procedure reset_dut is
        begin
            rst_n   <= '0';
            a_en    <= '0';
            a_we    <= '0';
            a_addr  <= (others => '0');
            a_wdata <= (others => '0');
            a_be    <= (others => '1');
            b_en    <= '0';
            b_addr  <= (others => '0');
            for i in 1 to 5 loop
                wait until rising_edge(clk);
            end loop;
            rst_n <= '1';
            wait until rising_edge(clk);
        end procedure;
        
    begin
        report "============================================";
        report "ALY Memory Testbench";
        report "============================================";
        report "";

        reset_dut;

        -- Test 1: Write and read back
        report "[TEST] Write/read operations";
        for i in 0 to 15 loop
            a_en    <= '1';
            a_we    <= '1';
            a_addr  <= std_logic_vector(to_unsigned(i, ADDR_WIDTH));
            a_wdata <= std_logic_vector(to_unsigned(i * 16#11111111#, WIDTH));
            a_be    <= (others => '1');
            wait until rising_edge(clk);
        end loop;
        a_we <= '0';
        
        for i in 0 to 15 loop
            a_addr <= std_logic_vector(to_unsigned(i, ADDR_WIDTH));
            wait until rising_edge(clk);
            wait until rising_edge(clk);  -- Extra cycle for read latency
            expected := std_logic_vector(to_unsigned(i * 16#11111111#, WIDTH));
            check("Read back addr " & integer'image(i) & " correct", a_rdata = expected);
        end loop;

        -- Test 2: Byte enable
        report "[TEST] Byte enable";
        a_we    <= '1';
        a_addr  <= (others => '0');
        a_wdata <= x"FFFFFFFF";
        a_be    <= "0001";  -- Only write byte 0
        wait until rising_edge(clk);
        a_we <= '0';
        wait until rising_edge(clk);
        wait until rising_edge(clk);
        check("Byte enable works", a_rdata(7 downto 0) = x"FF");

        -- Summary
        report "";
        report "============================================";
        report "Test Summary: " & integer'image(pass_count) & "/" & integer'image(test_count) & " passed";
        report "============================================";

        if fail_count = 0 then
            report "TEST PASSED";
        else
            report "TEST FAILED" severity failure;
        end if;

        sim_done <= true;
        wait;
    end process;

    -- Timeout
    timeout_proc: process
    begin
        wait for 1 ms;
        if not sim_done then
            report "[ERROR] Simulation timeout!" severity failure;
        end if;
        wait;
    end process;

end architecture sim;
