-- Testbench for Synchronous FIFO - VHDL
-- =============================================================================

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity tb_sync_fifo is
end entity tb_sync_fifo;

architecture sim of tb_sync_fifo is

    -- Parameters
    constant DATA_WIDTH : integer := 8;
    constant DEPTH      : integer := 16;
    constant ADDR_WIDTH : integer := integer(ceil(log2(real(DEPTH))));
    constant CLK_PERIOD : time := 10 ns;

    -- DUT signals
    signal clk     : std_logic := '0';
    signal rst_n   : std_logic := '0';
    signal wr_en   : std_logic := '0';
    signal wr_data : std_logic_vector(DATA_WIDTH-1 downto 0) := (others => '0');
    signal full    : std_logic;
    signal rd_en   : std_logic := '0';
    signal rd_data : std_logic_vector(DATA_WIDTH-1 downto 0);
    signal empty   : std_logic;
    signal count   : std_logic_vector(ADDR_WIDTH downto 0);

    -- Test control
    signal test_done : boolean := false;

begin

    -- Clock generation
    clk <= not clk after CLK_PERIOD/2 when not test_done else '0';

    -- DUT instantiation
    dut: entity work.sync_fifo
        generic map (
            DATA_WIDTH => DATA_WIDTH,
            DEPTH      => DEPTH
        )
        port map (
            clk     => clk,
            rst_n   => rst_n,
            wr_en   => wr_en,
            wr_data => wr_data,
            full    => full,
            rd_en   => rd_en,
            rd_data => rd_data,
            empty   => empty,
            count   => count
        );

    -- Test process
    test_proc: process
        variable errors : integer := 0;
        
        -- Expected FIFO model
        type fifo_array is array (0 to DEPTH-1) of std_logic_vector(DATA_WIDTH-1 downto 0);
        variable expected_fifo : fifo_array;
        variable expected_head : integer := 0;
        variable expected_tail : integer := 0;
        variable expected_count : integer := 0;
        
        procedure expect_push(data : std_logic_vector(DATA_WIDTH-1 downto 0)) is
        begin
            expected_fifo(expected_tail) := data;
            expected_tail := (expected_tail + 1) mod DEPTH;
            expected_count := expected_count + 1;
        end procedure;
        
        procedure expect_pop is
        begin
            expected_head := (expected_head + 1) mod DEPTH;
            expected_count := expected_count - 1;
        end procedure;
        
    begin
        report "=== Sync FIFO Testbench Started ===" severity note;
        
        -- Initialize
        rst_n <= '0';
        wr_en <= '0';
        rd_en <= '0';
        wr_data <= (others => '0');
        
        wait for CLK_PERIOD * 5;
        rst_n <= '1';
        wait for CLK_PERIOD;
        
        -- Test 1: Check initial state
        report "Test 1: Initial state" severity note;
        assert empty = '1' report "FIFO should be empty" severity error;
        assert full = '0' report "FIFO should not be full" severity error;
        assert unsigned(count) = 0 report "Count should be 0" severity error;
        if empty /= '1' or full /= '0' or unsigned(count) /= 0 then
            errors := errors + 1;
        end if;
        
        -- Test 2: Write single entry
        report "Test 2: Single write" severity note;
        wait until rising_edge(clk);
        wr_en <= '1';
        wr_data <= x"A5";
        expect_push(x"A5");
        wait until rising_edge(clk);
        wr_en <= '0';
        wait until rising_edge(clk);
        
        assert empty = '0' report "FIFO should not be empty" severity error;
        assert unsigned(count) = 1 report "Count should be 1" severity error;
        if empty /= '0' or unsigned(count) /= 1 then
            errors := errors + 1;
        end if;
        
        -- Test 3: Read single entry
        report "Test 3: Single read" severity note;
        rd_en <= '1';
        wait until rising_edge(clk);
        assert rd_data = expected_fifo(expected_head) report "Read data mismatch" severity error;
        if rd_data /= expected_fifo(expected_head) then
            errors := errors + 1;
        end if;
        expect_pop;
        rd_en <= '0';
        wait until rising_edge(clk);
        
        assert empty = '1' report "FIFO should be empty" severity error;
        if empty /= '1' then
            errors := errors + 1;
        end if;
        
        -- Test 4: Fill FIFO completely
        report "Test 4: Fill FIFO" severity note;
        for i in 0 to DEPTH-1 loop
            wr_en <= '1';
            wr_data <= std_logic_vector(to_unsigned(i, DATA_WIDTH));
            expect_push(std_logic_vector(to_unsigned(i, DATA_WIDTH)));
            wait until rising_edge(clk);
        end loop;
        wr_en <= '0';
        wait until rising_edge(clk);
        
        assert full = '1' report "FIFO should be full" severity error;
        assert unsigned(count) = DEPTH report "Count should equal DEPTH" severity error;
        if full /= '1' or unsigned(count) /= DEPTH then
            errors := errors + 1;
        end if;
        
        -- Test 5: Read all entries
        report "Test 5: Read all entries" severity note;
        for i in 0 to DEPTH-1 loop
            rd_en <= '1';
            wait until rising_edge(clk);
            assert rd_data = expected_fifo(expected_head) 
                report "Data mismatch at " & integer'image(i) severity error;
            if rd_data /= expected_fifo(expected_head) then
                errors := errors + 1;
            end if;
            expect_pop;
        end loop;
        rd_en <= '0';
        wait until rising_edge(clk);
        
        assert empty = '1' report "FIFO should be empty" severity error;
        if empty /= '1' then
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
        wait for 100 us;
        if not test_done then
            report "Timeout!" severity failure;
        end if;
        wait;
    end process;

end architecture sim;
