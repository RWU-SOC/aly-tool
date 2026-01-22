// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// UART Transmitter - Simple TX module
// 
// Basic UART transmitter with configurable baud rate.
// 8N1 format: 8 data bits, no parity, 1 stop bit
//-----------------------------------------------------------------------------
module uart_tx #(
    parameter CLK_FREQ = 100_000_000,  // Clock frequency in Hz
    parameter BAUD     = 115200        // Baud rate
)(
    input  wire       clk_i,
    input  wire       rst_ni,
    input  wire [7:0] data_i,      // Data to transmit
    input  wire       valid_i,     // Data valid, start transmission
    output wire       ready_o,     // Ready to accept data
    output wire       tx_o         // UART TX line
);

    localparam CLKS_PER_BIT = CLK_FREQ / BAUD;
    localparam CNT_WIDTH = $clog2(CLKS_PER_BIT);

    // State encoding
    localparam [2:0] IDLE  = 3'd0;
    localparam [2:0] START = 3'd1;
    localparam [2:0] DATA  = 3'd2;
    localparam [2:0] STOP  = 3'd3;

    reg [2:0]           state_q, state_d;
    reg [CNT_WIDTH-1:0] cnt_q;
    reg [2:0]           bit_idx_q;
    reg [7:0]           data_q;
    reg                 tx_q;

    // Next state logic
    always @(*) begin
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
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            state_q   <= IDLE;
            cnt_q     <= {CNT_WIDTH{1'b0}};
            bit_idx_q <= 3'b0;
            data_q    <= 8'b0;
            tx_q      <= 1'b1;
        end else begin
            state_q <= state_d;
            
            case (state_q)
                IDLE: begin
                    tx_q      <= 1'b1;
                    cnt_q     <= {CNT_WIDTH{1'b0}};
                    bit_idx_q <= 3'b0;
                    if (valid_i) begin
                        data_q <= data_i;
                    end
                end
                
                START: begin
                    tx_q <= 1'b0;  // Start bit
                    if (cnt_q < CLKS_PER_BIT - 1) begin
                        cnt_q <= cnt_q + 1'b1;
                    end else begin
                        cnt_q <= {CNT_WIDTH{1'b0}};
                    end
                end
                
                DATA: begin
                    tx_q <= data_q[bit_idx_q];
                    if (cnt_q < CLKS_PER_BIT - 1) begin
                        cnt_q <= cnt_q + 1'b1;
                    end else begin
                        cnt_q     <= {CNT_WIDTH{1'b0}};
                        bit_idx_q <= bit_idx_q + 1'b1;
                    end
                end
                
                STOP: begin
                    tx_q <= 1'b1;  // Stop bit
                    if (cnt_q < CLKS_PER_BIT - 1) begin
                        cnt_q <= cnt_q + 1'b1;
                    end else begin
                        cnt_q <= {CNT_WIDTH{1'b0}};
                    end
                end
                
                default: begin
                    tx_q <= 1'b1;
                end
            endcase
        end
    end

    assign ready_o = (state_q == IDLE);
    assign tx_o    = tx_q;

endmodule
