// CDC Bus Synchronizer - Verilog
// =============================================================================
// Multi-bit bus synchronizer using gray-code conversion.
// Safe for CDC when source value changes infrequently.
// =============================================================================

module cdc_sync_bus #(
    parameter WIDTH     = 8,    // Bus width
    parameter STAGES    = 2,    // Number of sync stages
    parameter RESET_VAL = 1'b0  // Reset value
)(
    // Source domain
    input  wire               clk_src,
    input  wire               rst_src_n,
    input  wire [WIDTH-1:0]   data_src,
    
    // Destination domain
    input  wire               clk_dst,
    input  wire               rst_dst_n,
    output wire [WIDTH-1:0]   data_dst
);

    integer i;

    // ==========================================================================
    // Source domain: Binary to Gray conversion
    // ==========================================================================
    wire [WIDTH-1:0] data_src_gray;
    reg  [WIDTH-1:0] data_src_gray_reg;
    
    // Binary to Gray conversion
    assign data_src_gray = data_src ^ (data_src >> 1);
    
    // Register in source domain
    always @(posedge clk_src or negedge rst_src_n) begin
        if (!rst_src_n) begin
            data_src_gray_reg <= {WIDTH{RESET_VAL}};
        end else begin
            data_src_gray_reg <= data_src_gray;
        end
    end

    // ==========================================================================
    // Synchronizer chain
    // ==========================================================================
    (* ASYNC_REG = "TRUE" *) reg [WIDTH-1:0] sync_chain_0;
    (* ASYNC_REG = "TRUE" *) reg [WIDTH-1:0] sync_chain_1;
    
    // Fixed 2-stage synchronizer for Verilog compatibility
    always @(posedge clk_dst or negedge rst_dst_n) begin
        if (!rst_dst_n) begin
            sync_chain_0 <= {WIDTH{RESET_VAL}};
            sync_chain_1 <= {WIDTH{RESET_VAL}};
        end else begin
            sync_chain_0 <= data_src_gray_reg;
            sync_chain_1 <= sync_chain_0;
        end
    end

    // ==========================================================================
    // Destination domain: Gray to Binary conversion
    // ==========================================================================
    wire [WIDTH-1:0] data_dst_gray;
    reg  [WIDTH-1:0] data_dst_bin;
    
    assign data_dst_gray = sync_chain_1;
    
    // Gray to Binary conversion
    always @(*) begin
        data_dst_bin[WIDTH-1] = data_dst_gray[WIDTH-1];
        for (i = WIDTH-2; i >= 0; i = i - 1) begin
            data_dst_bin[i] = data_dst_bin[i+1] ^ data_dst_gray[i];
        end
    end
    
    assign data_dst = data_dst_bin;

endmodule
