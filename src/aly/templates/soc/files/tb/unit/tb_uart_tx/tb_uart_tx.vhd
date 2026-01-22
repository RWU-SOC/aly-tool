-- Copyright 2025 ALY Project
-- SPDX-License-Identifier: Apache-2.0

-------------------------------------------------------------------------------
-- Testbench for UART TX Module (VHDL)
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity tb_uart_tx is
end entity tb_uart_tx;

architecture sim of tb_uart_tx is
    -- Parameters
    constant CLK_FREQ    : integer := 100_000_000;
    constant BAUD        : integer := 115200;
    constant CLK_PERIOD  : time := 10 ns;  -- 100 MHz
    constant CLKS_PER_BIT: integer := CLK_FREQ / BAUD;

    -- Signals
    signal clk   : std_logic := '0';
    signal rst_n : std_logic := '0';
    signal data  : std_logic_vector(7 downto 0) := (others => '0');
    signal valid : std_logic := '0';
    signal ready : std_logic;
    signal tx    : std_logic;
    
    -- Test tracking
    signal test_count : integer := 0;
    signal pass_count : integer := 0;
    signal fail_count : integer := 0;
    signal sim_done   : boolean := false;
    signal rx_data    : std_logic_vector(7 downto 0);

begin

    -- DUT instantiation
    dut: entity work.uart_tx
        generic map (
            CLK_FREQ => CLK_FREQ,
            BAUD     => BAUD
        )
        port map (
            clk_i   => clk,
            rst_ni  => rst_n,
            data_i  => data,
            valid_i => valid,
            ready_o => ready,
            tx_o    => tx
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
            data  <= (others => '0');
            valid <= '0';
            for i in 1 to 5 loop
                wait until rising_edge(clk);
            end loop;
            rst_n <= '1';
            wait until rising_edge(clk);
        end procedure;
        
    begin
        report "============================================";
        report "ALY UART TX Testbench";
        report "============================================";
        report "";

        reset_dut;

        -- Test 1: Initial state
        report "[TEST] Initial state";
        check("TX line idle high", tx = '1');
        check("Ready to transmit", ready = '1');

        -- Test 2: Transmit a byte
        report "[TEST] Transmit byte 0x55";
        data  <= x"55";
        valid <= '1';
        wait until rising_edge(clk);
        valid <= '0';
        
        -- Wait for start bit
        wait until tx = '0';
        check("Start bit detected", tx = '0');
        
        -- Sample data bits in the middle of each bit period
        rx_data <= (others => '0');
        for bit_idx in 0 to 7 loop
            for i in 1 to CLKS_PER_BIT loop
                wait until rising_edge(clk);
            end loop;
            rx_data(bit_idx) <= tx;
        end loop;
        
        -- Wait for stop bit
        for i in 1 to CLKS_PER_BIT loop
            wait until rising_edge(clk);
        end loop;
        check("Stop bit detected", tx = '1');
        check("Data transmitted correctly", rx_data = x"55");

        -- Wait for ready
        wait until ready = '1';
        check("Ready after transmission", ready = '1');

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
        wait for 50 ms;  -- 50ms timeout for slow baud rate
        if not sim_done then
            report "[ERROR] Simulation timeout!" severity failure;
        end if;
        wait;
    end process;

end architecture sim;
