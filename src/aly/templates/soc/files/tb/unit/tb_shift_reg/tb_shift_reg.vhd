-- Copyright 2025 ALY Project
-- SPDX-License-Identifier: Apache-2.0

-------------------------------------------------------------------------------
-- Testbench for Shift Register Module (VHDL)
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_shift_reg is
end entity tb_shift_reg;

architecture sim of tb_shift_reg is
    -- Parameters
    constant WIDTH     : integer := 8;
    constant CLK_PERIOD: time := 10 ns;

    -- Signals
    signal clk         : std_logic := '0';
    signal rst_n       : std_logic := '0';
    signal en          : std_logic := '0';
    signal dir         : std_logic := '0';
    signal load        : std_logic := '0';
    signal serial_in   : std_logic := '0';
    signal parallel_in : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
    signal data        : std_logic_vector(WIDTH-1 downto 0);
    signal serial_out  : std_logic;
    
    -- Test tracking
    signal test_count : integer := 0;
    signal pass_count : integer := 0;
    signal fail_count : integer := 0;
    signal sim_done   : boolean := false;

begin

    -- DUT instantiation
    dut: entity work.shift_reg
        generic map (
            WIDTH    => WIDTH,
            DEPTH    => 1,
            CIRCULAR => false
        )
        port map (
            clk_i      => clk,
            rst_ni     => rst_n,
            en_i       => en,
            dir_i      => dir,
            load_i     => load,
            serial_i   => serial_in,
            parallel_i => parallel_in,
            data_o     => data,
            serial_o   => serial_out
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
            rst_n       <= '0';
            en          <= '0';
            dir         <= '0';
            load        <= '0';
            serial_in   <= '0';
            parallel_in <= (others => '0');
            for i in 1 to 5 loop
                wait until rising_edge(clk);
            end loop;
            rst_n <= '1';
            wait until rising_edge(clk);
        end procedure;
        
    begin
        report "============================================";
        report "ALY Shift Register Testbench";
        report "============================================";
        report "";

        reset_dut;

        -- Test 1: Parallel load
        report "[TEST] Parallel load";
        parallel_in <= x"A5";
        load <= '1';
        wait until rising_edge(clk);
        load <= '0';
        wait until rising_edge(clk);
        check("Parallel load works", data = x"A5");

        -- Test 2: Left shift
        report "[TEST] Left shift";
        en <= '1';
        dir <= '0';  -- Left
        serial_in <= '1';
        wait until rising_edge(clk);
        check("Left shift works", data = x"4B");  -- A5 << 1 | 1 = 4B

        -- Test 3: Right shift
        report "[TEST] Right shift";
        dir <= '1';  -- Right
        serial_in <= '0';
        wait until rising_edge(clk);
        check("Right shift works", data = x"25");  -- 4B >> 1 = 25

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
        wait for 100 us;
        if not sim_done then
            report "[ERROR] Simulation timeout!" severity failure;
        end if;
        wait;
    end process;

end architecture sim;
