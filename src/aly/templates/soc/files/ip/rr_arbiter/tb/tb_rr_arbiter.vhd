-- Testbench for Round-Robin Arbiter - VHDL
-- =============================================================================

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_rr_arbiter is
end entity tb_rr_arbiter;

architecture sim of tb_rr_arbiter is

    -- Parameters
    constant NUM_REQ    : integer := 4;
    constant CLK_PERIOD : time := 10 ns;

    -- DUT signals
    signal clk    : std_logic := '0';
    signal rst_n  : std_logic := '0';
    signal req    : std_logic_vector(NUM_REQ-1 downto 0) := (others => '0');
    signal grant  : std_logic_vector(NUM_REQ-1 downto 0);
    signal enable : std_logic := '0';
    signal valid  : std_logic;

    -- Test control
    signal test_done : boolean := false;

    -- Helper function: count ones
    function count_ones(vec : std_logic_vector) return integer is
        variable cnt : integer := 0;
    begin
        for i in vec'range loop
            if vec(i) = '1' then
                cnt := cnt + 1;
            end if;
        end loop;
        return cnt;
    end function;

begin

    -- Clock generation
    clk <= not clk after CLK_PERIOD/2 when not test_done else '0';

    -- DUT instantiation
    dut: entity work.rr_arbiter
        generic map (
            NUM_REQ => NUM_REQ
        )
        port map (
            clk    => clk,
            rst_n  => rst_n,
            req    => req,
            grant  => grant,
            enable => enable,
            valid  => valid
        );

    -- Test process
    test_proc: process
        variable errors : integer := 0;
        type grant_count_array is array (0 to NUM_REQ-1) of integer;
        variable grant_count : grant_count_array := (others => 0);
    begin
        report "=== Round-Robin Arbiter Testbench ===" severity note;
        
        -- Initialize
        rst_n  <= '0';
        req    <= (others => '0');
        enable <= '0';
        
        wait for CLK_PERIOD * 5;
        rst_n <= '1';
        wait for CLK_PERIOD;
        
        -- Test 1: No requests
        report "Test 1: No requests" severity note;
        enable <= '1';
        req <= (others => '0');
        wait until rising_edge(clk);
        wait for 1 ns;
        
        assert valid = '0' report "Valid should be 0 with no requests" severity error;
        assert grant = "0000" report "Grant should be 0" severity error;
        if valid /= '0' or grant /= "0000" then
            errors := errors + 1;
        end if;
        
        -- Test 2: Single request
        report "Test 2: Single request" severity note;
        req <= "0010";  -- Request from port 1
        wait until rising_edge(clk);
        wait for 1 ns;
        
        assert valid = '1' report "Valid should be 1" severity error;
        assert grant = "0010" report "Grant should be on port 1" severity error;
        assert count_ones(grant) <= 1 report "Grant not one-hot" severity error;
        if valid /= '1' or grant /= "0010" then
            errors := errors + 1;
        end if;
        
        -- Test 3: Multiple requests - round robin
        report "Test 3: Round-robin behavior" severity note;
        req <= "1111";  -- All requests active
        
        -- Should cycle through all ports
        for cycle in 0 to 7 loop
            wait until rising_edge(clk);
            wait for 1 ns;
            
            assert valid = '1' report "Valid should be 1" severity error;
            assert count_ones(grant) <= 1 report "Grant not one-hot" severity error;
            
            -- Count grants
            for i in 0 to NUM_REQ-1 loop
                if grant(i) = '1' then
                    grant_count(i) := grant_count(i) + 1;
                end if;
            end loop;
        end loop;
        
        -- Print grant counts
        for i in 0 to NUM_REQ-1 loop
            report "  Port " & integer'image(i) & ": " & 
                   integer'image(grant_count(i)) & " grants" severity note;
        end loop;
        
        -- Test 4: Enable control
        report "Test 4: Enable control" severity note;
        enable <= '0';
        req <= "1111";
        wait until rising_edge(clk);
        wait for 1 ns;
        
        assert valid = '0' report "Valid should be 0 when disabled" severity error;
        assert grant = "0000" report "Grant should be 0 when disabled" severity error;
        if valid /= '0' or grant /= "0000" then
            errors := errors + 1;
        end if;
        
        enable <= '1';
        wait until rising_edge(clk);
        wait for 1 ns;
        
        assert valid = '1' report "Valid should be 1 when enabled" severity error;
        if valid /= '1' then
            errors := errors + 1;
        end if;
        
        -- Summary
        wait for CLK_PERIOD * 5;
        report "=== Test Complete ===" severity note;
        if errors = 0 then
            report "PASSED: All tests passed!" severity note;
        else
            report "FAILED: " & integer'image(errors) & " errors" severity error;
        end if;
        
        test_done <= true;
        wait;
    end process;

    -- Timeout watchdog
    watchdog: process
    begin
        wait for 50 us;
        if not test_done then
            report "Timeout!" severity failure;
        end if;
        wait;
    end process;

end architecture sim;
