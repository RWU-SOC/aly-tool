-- Copyright 2025 ALY Project
-- SPDX-License-Identifier: Apache-2.0

-------------------------------------------------------------------------------
-- Testbench for GPIO Module (VHDL)
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_gpio is
end entity tb_gpio;

architecture sim of tb_gpio is
    -- Parameters
    constant WIDTH     : integer := 8;
    constant CLK_PERIOD: time := 10 ns;

    -- Signals
    signal clk     : std_logic := '0';
    signal rst_n   : std_logic := '0';
    signal addr    : std_logic_vector(31 downto 0) := (others => '0');
    signal wdata   : std_logic_vector(31 downto 0) := (others => '0');
    signal we      : std_logic := '0';
    signal re      : std_logic := '0';
    signal rdata   : std_logic_vector(31 downto 0);
    signal gpio_in : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
    signal gpio_out: std_logic_vector(WIDTH-1 downto 0);
    signal gpio_oe : std_logic_vector(WIDTH-1 downto 0);
    
    -- Test tracking
    signal test_count : integer := 0;
    signal pass_count : integer := 0;
    signal fail_count : integer := 0;
    signal sim_done   : boolean := false;

begin

    -- DUT instantiation
    dut: entity work.gpio
        generic map (
            WIDTH => WIDTH
        )
        port map (
            clk_i     => clk,
            rst_ni    => rst_n,
            addr_i    => addr,
            wdata_i   => wdata,
            we_i      => we,
            re_i      => re,
            rdata_o   => rdata,
            gpio_i    => gpio_in,
            gpio_o    => gpio_out,
            gpio_oe_o => gpio_oe
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
            addr    <= (others => '0');
            wdata   <= (others => '0');
            we      <= '0';
            re      <= '0';
            gpio_in <= (others => '0');
            for i in 1 to 5 loop
                wait until rising_edge(clk);
            end loop;
            rst_n <= '1';
            wait until rising_edge(clk);
        end procedure;
        
    begin
        report "============================================";
        report "ALY GPIO Testbench";
        report "============================================";
        report "";

        reset_dut;

        -- Test 1: Write to data register
        report "[TEST] Data register write";
        addr  <= x"00000000";  -- REG_DATA
        wdata <= x"000000A5";
        we    <= '1';
        wait until rising_edge(clk);
        we <= '0';
        wait until rising_edge(clk);
        check("Data output correct", gpio_out = x"A5");

        -- Test 2: Write to direction register
        report "[TEST] Direction register write";
        addr  <= x"00000004";  -- REG_DIR
        wdata <= x"000000FF";
        we    <= '1';
        wait until rising_edge(clk);
        we <= '0';
        wait until rising_edge(clk);
        check("Direction output correct", gpio_oe = x"FF");

        -- Test 3: Read input register
        report "[TEST] Input register read";
        gpio_in <= x"5A";
        wait until rising_edge(clk);
        wait until rising_edge(clk);  -- Sync cycle
        addr <= x"00000008";  -- REG_INPUT
        re   <= '1';
        wait until rising_edge(clk);
        check("Input read correct", rdata(7 downto 0) = x"5A");
        re <= '0';

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
