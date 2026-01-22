// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// GPIO Module - Simple General Purpose I/O
// 
// Basic GPIO with configurable width and direction control.
//-----------------------------------------------------------------------------
module gpio #(
    parameter WIDTH = 8
)(
    input  wire             clk_i,
    input  wire             rst_ni,
    
    // Register interface
    input  wire [31:0]      addr_i,
    input  wire [31:0]      wdata_i,
    input  wire             we_i,
    input  wire             re_i,
    output reg  [31:0]      rdata_o,
    
    // GPIO pins
    input  wire [WIDTH-1:0] gpio_i,
    output wire [WIDTH-1:0] gpio_o,
    output wire [WIDTH-1:0] gpio_oe_o  // Output enable (active high)
);

    // Register addresses
    localparam [3:0] REG_DATA   = 4'h0;  // Data register
    localparam [3:0] REG_DIR    = 4'h4;  // Direction (1=output)
    localparam [3:0] REG_INPUT  = 4'h8;  // Read input pins

    reg [WIDTH-1:0] data_q;
    reg [WIDTH-1:0] dir_q;
    reg [WIDTH-1:0] input_sync_q;

    // Synchronize inputs
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            input_sync_q <= {WIDTH{1'b0}};
        end else begin
            input_sync_q <= gpio_i;
        end
    end

    // Register writes
    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            data_q <= {WIDTH{1'b0}};
            dir_q  <= {WIDTH{1'b0}};
        end else if (we_i) begin
            case (addr_i[3:0])
                REG_DATA: data_q <= wdata_i[WIDTH-1:0];
                REG_DIR:  dir_q  <= wdata_i[WIDTH-1:0];
                default: ;
            endcase
        end
    end

    // Register reads
    always @(*) begin
        rdata_o = 32'b0;
        if (re_i) begin
            case (addr_i[3:0])
                REG_DATA:  rdata_o = {{(32-WIDTH){1'b0}}, data_q};
                REG_DIR:   rdata_o = {{(32-WIDTH){1'b0}}, dir_q};
                REG_INPUT: rdata_o = {{(32-WIDTH){1'b0}}, input_sync_q};
                default:   rdata_o = 32'b0;
            endcase
        end
    end

    // Output assignments
    assign gpio_o    = data_q;
    assign gpio_oe_o = dir_q;

endmodule
