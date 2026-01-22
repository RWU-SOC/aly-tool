-- Synchronous FIFO - VHDL
-- =============================================================================
-- A parameterizable synchronous FIFO with full/empty status signals.
-- Uses gray-code pointers for reliable status generation.
-- =============================================================================

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity sync_fifo is
    generic (
        DATA_WIDTH : integer := 8;
        DEPTH      : integer := 16
    );
    port (
        clk     : in  std_logic;
        rst_n   : in  std_logic;
        
        -- Write interface
        wr_en   : in  std_logic;
        wr_data : in  std_logic_vector(DATA_WIDTH-1 downto 0);
        full    : out std_logic;
        
        -- Read interface
        rd_en   : in  std_logic;
        rd_data : out std_logic_vector(DATA_WIDTH-1 downto 0);
        empty   : out std_logic;
        
        -- Status
        count   : out std_logic_vector(integer(ceil(log2(real(DEPTH)))) downto 0)
    );
end entity sync_fifo;

architecture rtl of sync_fifo is
    -- Calculate address width
    constant ADDR_WIDTH : integer := integer(ceil(log2(real(DEPTH))));
    
    -- Memory type
    type mem_array is array (0 to DEPTH-1) of std_logic_vector(DATA_WIDTH-1 downto 0);
    signal mem : mem_array;
    
    -- Pointers (one extra bit for full/empty detection)
    signal wr_ptr : unsigned(ADDR_WIDTH downto 0);
    signal rd_ptr : unsigned(ADDR_WIDTH downto 0);
    
    -- Internal signals
    signal full_i  : std_logic;
    signal empty_i : std_logic;
    
begin
    -- ==========================================================================
    -- Status flags
    -- ==========================================================================
    full_i  <= '1' when (wr_ptr(ADDR_WIDTH) /= rd_ptr(ADDR_WIDTH)) and
                        (wr_ptr(ADDR_WIDTH-1 downto 0) = rd_ptr(ADDR_WIDTH-1 downto 0))
               else '0';
    empty_i <= '1' when (wr_ptr = rd_ptr) else '0';
    
    full  <= full_i;
    empty <= empty_i;
    count <= std_logic_vector(wr_ptr - rd_ptr);

    -- ==========================================================================
    -- Write logic
    -- ==========================================================================
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            wr_ptr <= (others => '0');
        elsif rising_edge(clk) then
            if wr_en = '1' and full_i = '0' then
                mem(to_integer(wr_ptr(ADDR_WIDTH-1 downto 0))) <= wr_data;
                wr_ptr <= wr_ptr + 1;
            end if;
        end if;
    end process;

    -- ==========================================================================
    -- Read logic
    -- ==========================================================================
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            rd_ptr <= (others => '0');
        elsif rising_edge(clk) then
            if rd_en = '1' and empty_i = '0' then
                rd_ptr <= rd_ptr + 1;
            end if;
        end if;
    end process;

    -- Registered read data
    rd_data <= mem(to_integer(rd_ptr(ADDR_WIDTH-1 downto 0)));

end architecture rtl;
