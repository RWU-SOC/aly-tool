-- Copyright 2025 ALY Project
-- SPDX-License-Identifier: Apache-2.0

-------------------------------------------------------------------------------
-- Testbench for MUX Module (VHDL)
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity tb_mux is
end entity tb_mux;

architecture sim of tb_mux is
    -- Parameters
    constant WIDTH    : integer := 8;
    constant N_INPUTS : integer := 4;
    constant SEL_WIDTH: integer := integer(ceil(log2(real(N_INPUTS))));

    -- Signals
    signal data : std_logic_vector(N_INPUTS*WIDTH-1 downto 0);
    signal sel  : std_logic_vector(SEL_WIDTH-1 downto 0);
    signal dout : std_logic_vector(WIDTH-1 downto 0);
    
    -- Test tracking
    signal test_count : integer := 0;
    signal pass_count : integer := 0;
    signal fail_count : integer := 0;

begin

    -- DUT instantiation
    dut: entity work.mux
        generic map (
            WIDTH    => WIDTH,
            N_INPUTS => N_INPUTS
        )
        port map (
            data_i => data,
            sel_i  => sel,
            data_o => dout
        );

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
        
    begin
        report "============================================";
        report "ALY MUX Testbench";
        report "============================================";
        report "";

        -- Initialize data inputs with distinct values
        data(1*WIDTH-1 downto 0*WIDTH) <= x"AA";
        data(2*WIDTH-1 downto 1*WIDTH) <= x"BB";
        data(3*WIDTH-1 downto 2*WIDTH) <= x"CC";
        data(4*WIDTH-1 downto 3*WIDTH) <= x"DD";

        -- Test each select value
        report "[TEST] Select operations";
        for i in 0 to N_INPUTS-1 loop
            sel <= std_logic_vector(to_unsigned(i, SEL_WIDTH));
            wait for 10 ns;
            expected := data((i+1)*WIDTH-1 downto i*WIDTH);
            check("MUX select " & integer'image(i) & " correct", dout = expected);
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

        wait;
    end process;

end architecture sim;
