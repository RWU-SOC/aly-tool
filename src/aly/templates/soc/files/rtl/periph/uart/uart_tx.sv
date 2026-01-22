// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// UART Transmitter - Simple TX module
// 
// Basic UART transmitter with configurable baud rate.
// 8N1 format: 8 data bits, no parity, 1 stop bit
//-----------------------------------------------------------------------------
module uart_tx #(
    parameter int CLK_FREQ = 100_000_000,  // Clock frequency in Hz
    parameter int BAUD     = 115200        // Baud rate
)(
    input  logic       clk_i,
    input  logic       rst_ni,
    input  logic [7:0] data_i,      // Data to transmit
    input  logic       valid_i,     // Data valid, start transmission
    output logic       ready_o,     // Ready to accept data
    output logic       tx_o         // UART TX line
);

    localparam int CLKS_PER_BIT = CLK_FREQ / BAUD;
    localparam int CNT_WIDTH = $clog2(CLKS_PER_BIT);

    typedef enum logic [2:0] {
        IDLE,
        START,
        DATA,
        STOP
    } state_t;

    state_t              state_q, state_d;
    logic [CNT_WIDTH-1:0] cnt_q;
    logic [2:0]          bit_idx_q;
    logic [7:0]          data_q;
    logic                tx_q;

    // Next state logic
    always_comb begin
        state_d = state_q;
        
        case (state_q)
            IDLE: begin
                if (valid_i) state_d = START;
            end
            START: begin
                if (cnt_q == CLKS_PER_BIT - 1) state_d = DATA;
            end
            DATA: begin
                if (cnt_q == CLKS_PER_BIT - 1 && bit_idx_q == 7) state_d = STOP;
            end
            STOP: begin
                if (cnt_q == CLKS_PER_BIT - 1) state_d = IDLE;
            end
            default: state_d = IDLE;
        endcase
    end

    // Sequential logic
    always_ff @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            state_q   <= IDLE;
            cnt_q     <= '0;
            bit_idx_q <= '0;
            data_q    <= '0;
            tx_q      <= 1'b1;
        end else begin
            state_q <= state_d;
            
            case (state_q)
                IDLE: begin
                    tx_q      <= 1'b1;
                    cnt_q     <= '0;
                    bit_idx_q <= '0;
                    if (valid_i) begin
                        data_q <= data_i;
                    end
                end
                
                START: begin
                    tx_q <= 1'b0;  // Start bit
                    if (cnt_q < CLKS_PER_BIT - 1) begin
                        cnt_q <= cnt_q + 1;
                    end else begin
                        cnt_q <= '0;
                    end
                end
                
                DATA: begin
                    tx_q <= data_q[bit_idx_q];
                    if (cnt_q < CLKS_PER_BIT - 1) begin
                        cnt_q <= cnt_q + 1;
                    end else begin
                        cnt_q     <= '0;
                        bit_idx_q <= bit_idx_q + 1;
                    end
                end
                
                STOP: begin
                    tx_q <= 1'b1;  // Stop bit
                    if (cnt_q < CLKS_PER_BIT - 1) begin
                        cnt_q <= cnt_q + 1;
                    end else begin
                        cnt_q <= '0;
                    end
                end
            endcase
        end
    end

    assign ready_o = (state_q == IDLE);
    assign tx_o    = tx_q;

endmodule : uart_tx
