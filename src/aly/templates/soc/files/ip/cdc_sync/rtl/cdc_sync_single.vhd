-- CDC Synchronizer (Single Bit) - VHDL
-- =============================================================================
-- Multi-stage flip-flop synchronizer for clock domain crossing.
-- Uses ASYNC_REG attribute for proper synthesis tool handling.
-- =============================================================================

library ieee;
use ieee.std_logic_1164.all;

entity cdc_sync_single is
    generic (
        STAGES    : integer := 2;    -- Number of sync stages
        RESET_VAL : std_logic := '0' -- Reset value
    );
    port (
        clk_dst   : in  std_logic;  -- Destination clock
        rst_dst_n : in  std_logic;  -- Destination reset (active low)
        data_src  : in  std_logic;  -- Source domain data
        data_dst  : out std_logic   -- Synchronized output
    );
end entity cdc_sync_single;

architecture rtl of cdc_sync_single is

    -- Synchronizer chain with ASYNC_REG attribute
    signal sync_chain : std_logic_vector(STAGES-1 downto 0);
    
    -- Synthesis attributes
    attribute ASYNC_REG : string;
    attribute ASYNC_REG of sync_chain : signal is "TRUE";

begin

    process(clk_dst, rst_dst_n)
    begin
        if rst_dst_n = '0' then
            sync_chain <= (others => RESET_VAL);
        elsif rising_edge(clk_dst) then
            sync_chain <= sync_chain(STAGES-2 downto 0) & data_src;
        end if;
    end process;

    data_dst <= sync_chain(STAGES-1);

end architecture rtl;
