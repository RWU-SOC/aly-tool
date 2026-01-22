-- Copyright 2025 ALY Project
-- SPDX-License-Identifier: Apache-2.0

-------------------------------------------------------------------------------
-- UART Transmitter - Simple TX module
-- 
-- Basic UART transmitter with configurable baud rate.
-- 8N1 format: 8 data bits, no parity, 1 stop bit
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity uart_tx is
    generic (
        CLK_FREQ : integer := 100_000_000;  -- Clock frequency in Hz
        BAUD     : integer := 115200        -- Baud rate
    );
    port (
        clk_i   : in  std_logic;
        rst_ni  : in  std_logic;
        data_i  : in  std_logic_vector(7 downto 0);  -- Data to transmit
        valid_i : in  std_logic;                     -- Data valid, start transmission
        ready_o : out std_logic;                     -- Ready to accept data
        tx_o    : out std_logic                      -- UART TX line
    );
end entity uart_tx;

architecture rtl of uart_tx is
    constant CLKS_PER_BIT : integer := CLK_FREQ / BAUD;
    constant CNT_WIDTH    : integer := integer(ceil(log2(real(CLKS_PER_BIT))));

    type state_t is (IDLE, START, DATA, STOP);
    
    signal state_q   : state_t;
    signal state_d   : state_t;
    signal cnt_q     : unsigned(CNT_WIDTH-1 downto 0);
    signal bit_idx_q : unsigned(2 downto 0);
    signal data_q    : std_logic_vector(7 downto 0);
    signal tx_q      : std_logic;
begin

    -- Next state logic
    process(state_q, valid_i, cnt_q, bit_idx_q)
    begin
        state_d <= state_q;
        
        case state_q is
            when IDLE =>
                if valid_i = '1' then
                    state_d <= START;
                end if;
            when START =>
                if cnt_q = CLKS_PER_BIT - 1 then
                    state_d <= DATA;
                end if;
            when DATA =>
                if cnt_q = CLKS_PER_BIT - 1 and bit_idx_q = 7 then
                    state_d <= STOP;
                end if;
            when STOP =>
                if cnt_q = CLKS_PER_BIT - 1 then
                    state_d <= IDLE;
                end if;
            when others =>
                state_d <= IDLE;
        end case;
    end process;

    -- Sequential logic
    process(clk_i, rst_ni)
    begin
        if rst_ni = '0' then
            state_q   <= IDLE;
            cnt_q     <= (others => '0');
            bit_idx_q <= (others => '0');
            data_q    <= (others => '0');
            tx_q      <= '1';
        elsif rising_edge(clk_i) then
            state_q <= state_d;
            
            case state_q is
                when IDLE =>
                    tx_q      <= '1';
                    cnt_q     <= (others => '0');
                    bit_idx_q <= (others => '0');
                    if valid_i = '1' then
                        data_q <= data_i;
                    end if;
                    
                when START =>
                    tx_q <= '0';  -- Start bit
                    if cnt_q < CLKS_PER_BIT - 1 then
                        cnt_q <= cnt_q + 1;
                    else
                        cnt_q <= (others => '0');
                    end if;
                    
                when DATA =>
                    tx_q <= data_q(to_integer(bit_idx_q));
                    if cnt_q < CLKS_PER_BIT - 1 then
                        cnt_q <= cnt_q + 1;
                    else
                        cnt_q     <= (others => '0');
                        bit_idx_q <= bit_idx_q + 1;
                    end if;
                    
                when STOP =>
                    tx_q <= '1';  -- Stop bit
                    if cnt_q < CLKS_PER_BIT - 1 then
                        cnt_q <= cnt_q + 1;
                    else
                        cnt_q <= (others => '0');
                    end if;
                    
                when others =>
                    tx_q <= '1';
            end case;
        end if;
    end process;

    ready_o <= '1' when state_q = IDLE else '0';
    tx_o    <= tx_q;

end architecture rtl;
