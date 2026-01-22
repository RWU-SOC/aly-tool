// CDC Bus Synchronizer - SystemVerilog
// =============================================================================
// Multi-bit bus synchronizer using gray-code conversion.
// Safe for CDC when source value changes infrequently.
// For fast-changing buses, use async FIFO instead.
// =============================================================================

module cdc_sync_bus #(
    parameter int WIDTH     = 8,     // Bus width
    parameter int STAGES    = 2,     // Number of sync stages
    parameter bit RESET_VAL = 1'b0   // Reset value
)(
    // Source domain
    input  logic               clk_src,
    input  logic               rst_src_n,
    input  logic [WIDTH-1:0]   data_src,
    
    // Destination domain
    input  logic               clk_dst,
    input  logic               rst_dst_n,
    output logic [WIDTH-1:0]   data_dst
);

    // ==========================================================================
    // Source domain: Binary to Gray conversion
    // ==========================================================================
    logic [WIDTH-1:0] data_src_gray;
    logic [WIDTH-1:0] data_src_gray_reg;
    
    // Binary to Gray conversion
    assign data_src_gray = data_src ^ (data_src >> 1);
    
    // Register in source domain
    always_ff @(posedge clk_src or negedge rst_src_n) begin
        if (!rst_src_n) begin
            data_src_gray_reg <= {WIDTH{RESET_VAL}};
        end else begin
            data_src_gray_reg <= data_src_gray;
        end
    end

    // ==========================================================================
    // Synchronizer chain
    // ==========================================================================
    (* ASYNC_REG = "TRUE" *) logic [WIDTH-1:0] sync_chain [STAGES-1:0];
    
    always_ff @(posedge clk_dst or negedge rst_dst_n) begin
        if (!rst_dst_n) begin
            for (int i = 0; i < STAGES; i++) begin
                sync_chain[i] <= {WIDTH{RESET_VAL}};
            end
        end else begin
            sync_chain[0] <= data_src_gray_reg;
            for (int i = 1; i < STAGES; i++) begin
                sync_chain[i] <= sync_chain[i-1];
            end
        end
    end

    // ==========================================================================
    // Destination domain: Gray to Binary conversion
    // ==========================================================================
    logic [WIDTH-1:0] data_dst_gray;
    logic [WIDTH-1:0] data_dst_bin;
    
    assign data_dst_gray = sync_chain[STAGES-1];
    
    // Gray to Binary conversion
    always_comb begin
        data_dst_bin[WIDTH-1] = data_dst_gray[WIDTH-1];
        for (int i = WIDTH-2; i >= 0; i--) begin
            data_dst_bin[i] = data_dst_bin[i+1] ^ data_dst_gray[i];
        end
    end
    
    assign data_dst = data_dst_bin;

endmodule
