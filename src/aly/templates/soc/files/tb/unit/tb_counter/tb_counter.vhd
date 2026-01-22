-- Copyright 2025 ALY Project
-- SPDX-License-Identifier: Apache-2.0

-------------------------------------------------------------------------------
-- Testbench for Counter Module (VHDL)
-- 
-- This is the "Hello World" testbench - if this passes, your ALY setup works!
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_counter is
end entity tb_counter;

architecture sim of tb_counter is
    -- Parameters
    constant WIDTH     : integer := 8;
    constant MAX_COUNT : integer := 10;  -- Small for quick testing
    constant CLK_PERIOD: time := 10 ns;  -- 100 MHz

    -- Signals
    signal clk      : std_logic := '0';
    signal rst_n    : std_logic := '0';
    signal en       : std_logic := '0';
    signal clear    : std_logic := '0';
    signal count    : std_logic_vector(WIDTH-1 downto 0);
    signal overflow : std_logic;
    
    -- Test tracking
    signal test_count : integer := 0;
    signal pass_count : integer := 0;
    signal fail_count : integer := 0;
    signal sim_done   : boolean := false;

begin

    -- DUT instantiation
    dut: entity work.counter
        generic map (
            WIDTH     => WIDTH,
            MAX_COUNT => MAX_COUNT
        )
        port map (
            clk_i      => clk,
            rst_ni     => rst_n,
            en_i       => en,
            clear_i    => clear,
            count_o    => count,
            overflow_o => overflow
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
            rst_n <= '0';
            en    <= '0';
            clear <= '0';
            for i in 1 to 5 loop
                wait until rising_edge(clk);
            end loop;
            rst_n <= '1';
            wait until rising_edge(clk);
        end procedure;
        
    begin
        report "============================================";
        report "ALY Counter Testbench - Hello World Test";
        report "============================================";
        report "";

        -- Initialize
        reset_dut;

        -- Test 1: Counter stays at 0 when disabled
        report "[TEST] Counter disabled";
        en <= '0';
        for i in 1 to 10 loop
            wait until rising_edge(clk);
        end loop;
        check("Counter stays at 0 when disabled", unsigned(count) = 0);

        -- Test 2: Counter increments when enabled
        report "[TEST] Counter enable";
        en <= '1';
        for i in 1 to 5 loop
            wait until rising_edge(clk);
        end loop;
        check("Counter increments when enabled", unsigned(count) = 5);

        -- Test 3: Counter wraps at MAX_COUNT
        report "[TEST] Counter overflow";
        for i in 1 to 6 loop
            wait until rising_edge(clk);
        end loop;
        check("Counter wrapped around", unsigned(count) < 6);

        -- Test 4: Clear works
        report "[TEST] Clear function";
        clear <= '1';
        wait until rising_edge(clk);
        clear <= '0';
        wait until rising_edge(clk);
        check("Clear resets counter", unsigned(count) = 1);

        -- Test 5: Reset works
        report "[TEST] Reset";
        rst_n <= '0';
        wait until rising_edge(clk);
        check("Reset clears counter", unsigned(count) = 0);

        -- Summary
        report "";
        report "============================================";
        report "Test Summary: " & integer'image(pass_count) & "/" & integer'image(test_count) & " passed";
        report "============================================";

        if fail_count = 0 then
            report "";
            report "**********************************";
            report "*        TEST PASSED             *";
            report "*   ALY simulation is working!   *";
            report "**********************************";
            report "";
        else
            report "";
            report "**********************************";
            report "*        TEST FAILED             *";
            report "**********************************" severity failure;
            report "";
        end if;

        sim_done <= true;
        wait;
    end process;

    -- Timeout
    timeout_proc: process
    begin
        wait for 100 us;
        if not sim_done then
            report "[ERROR] Simulation timeout!" severity failure;
        end if;
        wait;
    end process;

end architecture sim;
