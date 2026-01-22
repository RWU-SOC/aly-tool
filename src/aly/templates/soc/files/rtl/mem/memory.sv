// Copyright 2025 ALY Project
// SPDX-License-Identifier: Apache-2.0

//-----------------------------------------------------------------------------
// Simple Memory Module with File Loading
// 
// A parameterized memory with:
// - Configurable depth and width
// - Optional initialization from .mem file
// - Single port or dual port modes
// - Byte enable support
//-----------------------------------------------------------------------------
module memory #(
    parameter int WIDTH     = 32,
    parameter int DEPTH     = 256,
    parameter     MEM_FILE  = "",      // Memory initialization file
    parameter bit DUAL_PORT = 0        // Enable second read port
)(
    input  logic                       clk_i,
    input  logic                       rst_ni,
    
    // Port A (read/write)
    input  logic                       a_en_i,
    input  logic                       a_we_i,
    input  logic [$clog2(DEPTH)-1:0]   a_addr_i,
    input  logic [WIDTH-1:0]           a_wdata_i,
    input  logic [WIDTH/8-1:0]         a_be_i,      // Byte enables
    output logic [WIDTH-1:0]           a_rdata_o,
    
    // Port B (read only, active when DUAL_PORT=1)
    input  logic                       b_en_i,
    input  logic [$clog2(DEPTH)-1:0]   b_addr_i,
    output logic [WIDTH-1:0]           b_rdata_o
);

    // Memory array
    logic [WIDTH-1:0] mem [DEPTH];
    
    // Initialize from file if specified
    initial begin
        if (MEM_FILE != "") begin
            $readmemh(MEM_FILE, mem);
            $display("[MEM] Loaded memory from %s", MEM_FILE);
        end
    end
    
    // Port A logic
    always_ff @(posedge clk_i) begin
        if (a_en_i) begin
            if (a_we_i) begin
                // Byte-enable write
                for (int i = 0; i < WIDTH/8; i++) begin
                    if (a_be_i[i]) begin
                        mem[a_addr_i][i*8 +: 8] <= a_wdata_i[i*8 +: 8];
                    end
                end
            end
            a_rdata_o <= mem[a_addr_i];
        end
    end
    
    // Port B logic (read-only)
    generate
        if (DUAL_PORT) begin : gen_port_b
            always_ff @(posedge clk_i) begin
                if (b_en_i) begin
                    b_rdata_o <= mem[b_addr_i];
                end
            end
        end else begin : gen_no_port_b
            assign b_rdata_o = '0;
        end
    endgenerate

endmodule

//-----------------------------------------------------------------------------
// ROM Module - Read-Only Memory with File Loading
//-----------------------------------------------------------------------------
module rom #(
    parameter int WIDTH    = 32,
    parameter int DEPTH    = 256,
    parameter     MEM_FILE = ""
)(
    input  logic                     clk_i,
    input  logic                     en_i,
    input  logic [$clog2(DEPTH)-1:0] addr_i,
    output logic [WIDTH-1:0]         data_o
);

    logic [WIDTH-1:0] mem [DEPTH];
    
    initial begin
        if (MEM_FILE != "") begin
            $readmemh(MEM_FILE, mem);
            $display("[ROM] Loaded ROM from %s", MEM_FILE);
        end else begin
            $display("[ROM] Warning: No MEM_FILE specified");
        end
    end
    
    always_ff @(posedge clk_i) begin
        if (en_i) begin
            data_o <= mem[addr_i];
        end
    end

endmodule
