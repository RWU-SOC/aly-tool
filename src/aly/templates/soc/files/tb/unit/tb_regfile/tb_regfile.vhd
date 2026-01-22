-- Copyright 2025 ALY Project
-- SPDX-License-Identifier: Apache-2.0

-------------------------------------------------------------------------------
-- Testbench for Register File Module (VHDL)
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity tb_regfile is
end entity tb_regfile;

architecture sim of tb_regfile is
    -- Parameters
    constant WIDTH      : integer := 32;
    constant DEPTH      : integer := 32;
    constant READ_PORTS : integer := 2;
    constant CLK_PERIOD : time := 10 ns;
    constant ADDR_WIDTH : integer := integer(ceil(log2(real(DEPTH))));

    -- Signals
    signal clk     : std_logic := '0';
    signal rst_n   : std_logic := '0';
    signal wr_en   : std_logic := '0';
    signal wr_addr : std_logic_vector(ADDR_WIDTH-1 downto 0) := (others => '0');
    signal wr_data : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
    signal rd_addr : std_logic_vector(READ_PORTS*ADDR_WIDTH-1 downto 0) := (others => '0');
    signal rd_data : std_logic_vector(READ_PORTS*WIDTH-1 downto 0);
    
    -- Test tracking
    signal test_count : integer := 0;
    signal pass_count : integer := 0;
    signal fail_count : integer := 0;
    signal sim_done   : boolean := false;

begin

    -- DUT instantiation
    dut: entity work.regfile
        generic map (
            WIDTH      => WIDTH,
            DEPTH      => DEPTH,
            ZERO_REG   => true,
            READ_PORTS => READ_PORTS
        )
        port map (
            clk_i     => clk,
            rst_ni    => rst_n,
            wr_en_i   => wr_en,
            wr_addr_i => wr_addr,
            wr_data_i => wr_data,
            rd_addr_i => rd_addr,
            rd_data_o => rd_data
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
            wr_en   <= '0';
            wr_addr <= (others => '0');
            wr_data <= (others => '0');
            rd_addr <= (others => '0');
            for i in 1 to 5 loop
                wait until rising_edge(clk);
            end loop;
            rst_n <= '1';
            wait until rising_edge(clk);
        end procedure;
        
    begin
        report "============================================";
        report "ALY Register File Testbench";
        report "============================================";
        report "";

        reset_dut;

        -- Test 1: Register 0 always reads as 0
        report "[TEST] Zero register";
        wr_en   <= '1';
        wr_addr <= (others => '0');
        wr_data <= x"DEADBEEF";
        wait until rising_edge(clk);
        wr_en <= '0';
        rd_addr(ADDR_WIDTH-1 downto 0) <= (others => '0');
        wait until rising_edge(clk);
        check("Register 0 reads as 0", rd_data(WIDTH-1 downto 0) = x"00000000");

        -- Test 2: Write and read back
        report "[TEST] Write/read operations";
        for i in 1 to 7 loop
            wr_en   <= '1';
            wr_addr <= std_logic_vector(to_unsigned(i, ADDR_WIDTH));
            wr_data <= std_logic_vector(to_unsigned(i * 16#11111111#, WIDTH));
            wait until rising_edge(clk);
        end loop;
        wr_en <= '0';
        
        for i in 1 to 7 loop
            rd_addr(ADDR_WIDTH-1 downto 0) <= std_logic_vector(to_unsigned(i, ADDR_WIDTH));
            wait until rising_edge(clk);
            expected := std_logic_vector(to_unsigned(i * 16#11111111#, WIDTH));
            check("Read back reg " & integer'image(i) & " correct", rd_data(WIDTH-1 downto 0) = expected);
        end loop;

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
