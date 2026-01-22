-- CDC Bus Synchronizer - VHDL
-- =============================================================================
-- Multi-bit bus synchronizer using gray-code conversion.
-- Safe for CDC when source value changes infrequently.
-- =============================================================================

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity cdc_sync_bus is
    generic (
        WIDTH     : integer := 8;     -- Bus width
        STAGES    : integer := 2;     -- Number of sync stages
        RESET_VAL : std_logic := '0'  -- Reset value
    );
    port (
        -- Source domain
        clk_src   : in  std_logic;
        rst_src_n : in  std_logic;
        data_src  : in  std_logic_vector(WIDTH-1 downto 0);
        
        -- Destination domain
        clk_dst   : in  std_logic;
        rst_dst_n : in  std_logic;
        data_dst  : out std_logic_vector(WIDTH-1 downto 0)
    );
end entity cdc_sync_bus;

architecture rtl of cdc_sync_bus is

    -- Gray code conversion functions
    function bin_to_gray(bin : std_logic_vector) return std_logic_vector is
        variable gray : std_logic_vector(bin'range);
    begin
        gray := bin xor ('0' & bin(bin'high downto bin'low+1));
        return gray;
    end function;
    
    function gray_to_bin(gray : std_logic_vector) return std_logic_vector is
        variable bin : std_logic_vector(gray'range);
    begin
        bin(gray'high) := gray(gray'high);
        for i in gray'high-1 downto gray'low loop
            bin(i) := bin(i+1) xor gray(i);
        end loop;
        return bin;
    end function;

    -- Source domain signals
    signal data_src_gray     : std_logic_vector(WIDTH-1 downto 0);
    signal data_src_gray_reg : std_logic_vector(WIDTH-1 downto 0);
    
    -- Synchronizer signals
    type sync_array is array (0 to STAGES-1) of std_logic_vector(WIDTH-1 downto 0);
    signal sync_chain : sync_array;
    
    -- Synthesis attributes
    attribute ASYNC_REG : string;
    attribute ASYNC_REG of sync_chain : signal is "TRUE";
    
    -- Destination domain signals
    signal data_dst_gray : std_logic_vector(WIDTH-1 downto 0);

begin

    -- ==========================================================================
    -- Source domain: Binary to Gray conversion
    -- ==========================================================================
    data_src_gray <= bin_to_gray(data_src);
    
    process(clk_src, rst_src_n)
    begin
        if rst_src_n = '0' then
            data_src_gray_reg <= (others => RESET_VAL);
        elsif rising_edge(clk_src) then
            data_src_gray_reg <= data_src_gray;
        end if;
    end process;

    -- ==========================================================================
    -- Synchronizer chain
    -- ==========================================================================
    process(clk_dst, rst_dst_n)
    begin
        if rst_dst_n = '0' then
            for i in 0 to STAGES-1 loop
                sync_chain(i) <= (others => RESET_VAL);
            end loop;
        elsif rising_edge(clk_dst) then
            sync_chain(0) <= data_src_gray_reg;
            for i in 1 to STAGES-1 loop
                sync_chain(i) <= sync_chain(i-1);
            end loop;
        end if;
    end process;

    -- ==========================================================================
    -- Destination domain: Gray to Binary conversion
    -- ==========================================================================
    data_dst_gray <= sync_chain(STAGES-1);
    data_dst <= gray_to_bin(data_dst_gray);

end architecture rtl;
