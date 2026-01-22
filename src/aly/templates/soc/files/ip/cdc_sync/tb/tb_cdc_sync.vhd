-- Testbench for CDC Synchronizers - VHDL
-- =============================================================================

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_cdc_sync is
end entity tb_cdc_sync;

architecture sim of tb_cdc_sync is

    -- Parameters
    constant STAGES         : integer := 2;
    constant WIDTH          : integer := 8;
    constant SRC_CLK_PERIOD : time := 10 ns;
    constant DST_CLK_PERIOD : time := 7 ns;

    -- Signals
    signal clk_src         : std_logic := '0';
    signal clk_dst         : std_logic := '0';
    signal rst_n           : std_logic := '0';
    signal data_src_single : std_logic := '0';
    signal data_dst_single : std_logic;
    signal data_src_bus    : std_logic_vector(WIDTH-1 downto 0) := (others => '0');
    signal data_dst_bus    : std_logic_vector(WIDTH-1 downto 0);

    -- Test control
    signal test_done : boolean := false;

begin

    -- Clock generation
    clk_src <= not clk_src after SRC_CLK_PERIOD/2 when not test_done else '0';
    clk_dst <= not clk_dst after DST_CLK_PERIOD/2 when not test_done else '0';

    -- DUT: Single-bit synchronizer
    dut_single: entity work.cdc_sync_single
        generic map (
            STAGES    => STAGES,
            RESET_VAL => '0'
        )
        port map (
            clk_dst   => clk_dst,
            rst_dst_n => rst_n,
            data_src  => data_src_single,
            data_dst  => data_dst_single
        );

    -- DUT: Bus synchronizer
    dut_bus: entity work.cdc_sync_bus
        generic map (
            WIDTH     => WIDTH,
            STAGES    => STAGES,
            RESET_VAL => '0'
        )
        port map (
            clk_src   => clk_src,
            rst_src_n => rst_n,
            data_src  => data_src_bus,
            clk_dst   => clk_dst,
            rst_dst_n => rst_n,
            data_dst  => data_dst_bus
        );

    -- Test process
    test_proc: process
        variable errors : integer := 0;
    begin
        report "=== CDC Synchronizer Testbench ===" severity note;
        
        -- Initialize
        rst_n <= '0';
        data_src_single <= '0';
        data_src_bus <= (others => '0');
        
        -- Reset
        for i in 0 to 9 loop
            wait until rising_edge(clk_dst);
        end loop;
        rst_n <= '1';
        for i in 0 to 4 loop
            wait until rising_edge(clk_dst);
        end loop;

        -- Test 1: Single-bit synchronizer
        report "Test 1: Single-bit synchronizer" severity note;
        
        wait until rising_edge(clk_src);
        data_src_single <= '1';
        for i in 0 to STAGES+1 loop
            wait until rising_edge(clk_dst);
        end loop;
        
        assert data_dst_single = '1' 
            report "Single-bit sync failed: expected 1" severity error;
        if data_dst_single /= '1' then
            errors := errors + 1;
        end if;
        
        wait until rising_edge(clk_src);
        data_src_single <= '0';
        for i in 0 to STAGES+1 loop
            wait until rising_edge(clk_dst);
        end loop;
        
        assert data_dst_single = '0' 
            report "Single-bit sync failed: expected 0" severity error;
        if data_dst_single /= '0' then
            errors := errors + 1;
        end if;

        -- Test 2: Bus synchronizer
        report "Test 2: Bus synchronizer" severity note;
        
        wait until rising_edge(clk_src);
        data_src_bus <= x"A5";
        for i in 0 to STAGES+4 loop
            wait until rising_edge(clk_dst);
        end loop;
        
        assert data_dst_bus = x"A5" 
            report "Bus sync failed: expected A5" severity error;
        if data_dst_bus /= x"A5" then
            errors := errors + 1;
        end if;

        -- Test 3: Toggle test
        report "Test 3: Toggle test" severity note;
        
        for i in 0 to 9 loop
            wait until rising_edge(clk_src);
            data_src_single <= not data_src_single;
            for j in 0 to STAGES loop
                wait until rising_edge(clk_dst);
            end loop;
        end loop;

        -- Test 4: Counter pattern
        report "Test 4: Counter pattern" severity note;
        
        for i in 0 to 31 loop
            wait until rising_edge(clk_src);
            data_src_bus <= std_logic_vector(to_unsigned(i, WIDTH));
            wait until rising_edge(clk_dst);
            wait until rising_edge(clk_dst);
        end loop;
        
        wait until rising_edge(clk_src);
        data_src_bus <= x"55";
        for i in 0 to STAGES+4 loop
            wait until rising_edge(clk_dst);
        end loop;
        
        assert data_dst_bus = x"55" 
            report "Counter test failed: expected 55" severity error;
        if data_dst_bus /= x"55" then
            errors := errors + 1;
        end if;

        -- Summary
        for i in 0 to 9 loop
            wait until rising_edge(clk_dst);
        end loop;
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
        wait for 100 us;
        if not test_done then
            report "Timeout!" severity failure;
        end if;
        wait;
    end process;

end architecture sim;
