-- Copyright 2025 ALY Project
-- SPDX-License-Identifier: Apache-2.0

-------------------------------------------------------------------------------
-- Testbench for FIFO Module (VHDL)
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity tb_fifo is
end entity tb_fifo;

architecture sim of tb_fifo is
    -- Parameters
    constant WIDTH     : integer := 8;
    constant DEPTH     : integer := 8;
    constant CLK_PERIOD: time := 10 ns;
    constant CNT_WIDTH : integer := integer(ceil(log2(real(DEPTH+1))));

    -- Signals
    signal clk          : std_logic := '0';
    signal rst_n        : std_logic := '0';
    signal wr_en        : std_logic := '0';
    signal wr_data      : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
    signal full         : std_logic;
    signal almost_full  : std_logic;
    signal rd_en        : std_logic := '0';
    signal rd_data      : std_logic_vector(WIDTH-1 downto 0);
    signal empty        : std_logic;
    signal almost_empty : std_logic;
    signal count        : std_logic_vector(CNT_WIDTH-1 downto 0);
    
    -- Test tracking
    signal test_count : integer := 0;
    signal pass_count : integer := 0;
    signal fail_count : integer := 0;
    signal sim_done   : boolean := false;

begin

    -- DUT instantiation
    dut: entity work.fifo
        generic map (
            WIDTH              => WIDTH,
            DEPTH              => DEPTH,
            ALMOST_FULL_THRESH => DEPTH-2,
            ALMOST_EMPTY_THRESH=> 2
        )
        port map (
            clk_i          => clk,
            rst_ni         => rst_n,
            wr_en_i        => wr_en,
            wr_data_i      => wr_data,
            full_o         => full,
            almost_full_o  => almost_full,
            rd_en_i        => rd_en,
            rd_data_o      => rd_data,
            empty_o        => empty,
            almost_empty_o => almost_empty,
            count_o        => count
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
            rst_n   <= '0';
            wr_en   <= '0';
            wr_data <= (others => '0');
            rd_en   <= '0';
            for i in 1 to 5 loop
                wait until rising_edge(clk);
            end loop;
            rst_n <= '1';
            wait until rising_edge(clk);
        end procedure;
        
    begin
        report "============================================";
        report "ALY FIFO Testbench";
        report "============================================";
        report "";

        reset_dut;

        -- Test 1: FIFO starts empty
        report "[TEST] Initial state";
        check("FIFO starts empty", empty = '1');
        check("FIFO not full", full = '0');

        -- Test 2: Write data
        report "[TEST] Write operations";
        for i in 0 to DEPTH-1 loop
            wr_en   <= '1';
            wr_data <= std_logic_vector(to_unsigned(i, WIDTH));
            wait until rising_edge(clk);
        end loop;
        wr_en <= '0';
        wait until rising_edge(clk);
        check("FIFO is full after writes", full = '1');
        check("FIFO not empty", empty = '0');

        -- Test 3: Read data
        report "[TEST] Read operations";
        for i in 0 to DEPTH-1 loop
            rd_en <= '1';
            wait until rising_edge(clk);
            check("Read data matches", rd_data = std_logic_vector(to_unsigned(i, WIDTH)));
        end loop;
        rd_en <= '0';
        wait until rising_edge(clk);
        check("FIFO is empty after reads", empty = '1');

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
