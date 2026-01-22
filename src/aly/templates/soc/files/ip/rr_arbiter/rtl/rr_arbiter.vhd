-- Round-Robin Arbiter - VHDL
-- =============================================================================
-- A fair round-robin arbiter with configurable number of request inputs.
-- Grants are issued in round-robin order, with priority rotating after each grant.
-- =============================================================================

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity rr_arbiter is
    generic (
        NUM_REQ : integer := 4
    );
    port (
        clk    : in  std_logic;
        rst_n  : in  std_logic;
        
        -- Request/Grant interface
        req    : in  std_logic_vector(NUM_REQ-1 downto 0);
        grant  : out std_logic_vector(NUM_REQ-1 downto 0);
        
        -- Control
        enable : in  std_logic;
        valid  : out std_logic
    );
end entity rr_arbiter;

architecture rtl of rr_arbiter is
    
    constant REQ_WIDTH : integer := integer(ceil(log2(real(NUM_REQ))));
    
    signal last_grant     : unsigned(REQ_WIDTH-1 downto 0);
    signal mask           : std_logic_vector(NUM_REQ-1 downto 0);
    signal masked_req     : std_logic_vector(NUM_REQ-1 downto 0);
    signal masked_grant   : std_logic_vector(NUM_REQ-1 downto 0);
    signal unmasked_grant : std_logic_vector(NUM_REQ-1 downto 0);
    signal masked_valid   : std_logic;
    signal valid_i        : std_logic;
    signal grant_i        : std_logic_vector(NUM_REQ-1 downto 0);
    
begin

    -- ==========================================================================
    -- Generate mask based on last grant
    -- ==========================================================================
    process(last_grant)
    begin
        mask <= (others => '0');
        for i in 0 to NUM_REQ-1 loop
            if i > to_integer(last_grant) then
                mask(i) <= '1';
            end if;
        end loop;
    end process;
    
    -- Masked requests
    masked_req <= req and mask;
    
    -- ==========================================================================
    -- Priority encoder for masked requests
    -- ==========================================================================
    process(masked_req)
        variable found : boolean;
    begin
        masked_grant <= (others => '0');
        found := false;
        for i in 0 to NUM_REQ-1 loop
            if masked_req(i) = '1' and not found then
                masked_grant(i) <= '1';
                found := true;
            end if;
        end loop;
    end process;
    
    masked_valid <= '1' when unsigned(masked_req) /= 0 else '0';
    
    -- ==========================================================================
    -- Priority encoder for unmasked requests (wrap-around)
    -- ==========================================================================
    process(req)
        variable found : boolean;
    begin
        unmasked_grant <= (others => '0');
        found := false;
        for i in 0 to NUM_REQ-1 loop
            if req(i) = '1' and not found then
                unmasked_grant(i) <= '1';
                found := true;
            end if;
        end loop;
    end process;
    
    -- ==========================================================================
    -- Select grant
    -- ==========================================================================
    grant_i <= masked_grant when masked_valid = '1' else unmasked_grant;
    grant   <= grant_i when enable = '1' else (others => '0');
    
    valid_i <= '1' when enable = '1' and unsigned(req) /= 0 else '0';
    valid   <= valid_i;
    
    -- ==========================================================================
    -- Update last grant
    -- ==========================================================================
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            last_grant <= (others => '0');
        elsif rising_edge(clk) then
            if valid_i = '1' then
                for i in 0 to NUM_REQ-1 loop
                    if grant_i(i) = '1' then
                        last_grant <= to_unsigned(i, REQ_WIDTH);
                    end if;
                end loop;
            end if;
        end if;
    end process;

end architecture rtl;
